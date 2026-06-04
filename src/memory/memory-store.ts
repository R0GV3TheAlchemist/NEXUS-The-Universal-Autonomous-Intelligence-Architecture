// src/memory/memory-store.ts
// GAIA-OS — Persistent Memory Store
// Canon ref: C01, Crystal Memory Architecture, SOVEREIGNTY.md
// Issue: #222
//
// "To remember is to remain." — GAIA Canon

export type MemoryTier = "core" | "episodic" | "semantic" | "working" | "procedural";
export type MemoryStatus = "active" | "archived" | "pending_review" | "flagged";

export interface MemoryEntry {
  id: string;
  key: string;
  value: unknown;
  tier: MemoryTier;
  tags: string[];
  created_at: string;
  updated_at: string;
  accessed_at: string;
  access_count: number;
  session_id: string;
  source: string;
  summary: string;
  status: MemoryStatus;
  ttl?: number;
  linked_memories?: string[];
}

export interface MemoryWriteOptions {
  tier?: MemoryTier;
  tags?: string[];
  source?: string;
  summary?: string;
  ttl?: number;
  linked_memories?: string[];
}

export interface MemoryQueryOptions {
  tier?: MemoryTier;
  tag?: string;
  status?: MemoryStatus;
  session_id?: string;
  since?: string;
  limit?: number;
  include_archived?: boolean;
}

export interface MemoryQueryResult {
  entries: MemoryEntry[];
  total: number;
  tiers: Record<MemoryTier, number>;
}

export interface MemoryStats {
  total_entries: number;
  by_tier: Record<MemoryTier, number>;
  by_status: Record<MemoryStatus, number>;
  oldest_entry: string | null;
  newest_entry: string | null;
  total_access_count: number;
}

function generateId(): string {
  return `mem-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

const TIER_PRIORITY: Record<MemoryTier, number> = { core: 0, episodic: 1, semantic: 2, procedural: 3, working: 4 };

export class MemoryStore {
  private store: Map<string, MemoryEntry> = new Map();
  private keyIndex: Map<string, string> = new Map();

  write(key: string, value: unknown, sessionId: string, opts: MemoryWriteOptions = {}): MemoryEntry {
    const existing = this.getByKey(key);
    const now = new Date().toISOString();
    if (existing) {
      const updated = { ...existing, value, updated_at: now, tags: opts.tags ?? existing.tags, summary: opts.summary ?? existing.summary, ttl: opts.ttl ?? existing.ttl, linked_memories: opts.linked_memories ?? existing.linked_memories };
      this.store.set(existing.id, updated);
      return updated;
    }
    const entry: MemoryEntry = { id: generateId(), key, value, tier: opts.tier ?? "semantic", tags: opts.tags ?? [], created_at: now, updated_at: now, accessed_at: now, access_count: 0, session_id: sessionId, source: opts.source ?? "gaia-agent", summary: opts.summary ?? String(key), status: "active", ttl: opts.ttl, linked_memories: opts.linked_memories ?? [] };
    this.store.set(entry.id, entry);
    this.keyIndex.set(key, entry.id);
    return entry;
  }

  read(key: string): MemoryEntry | undefined {
    const entry = this.getByKey(key);
    if (!entry) return undefined;
    if (this.isExpired(entry)) { this.expire(entry.id); return undefined; }
    const updated = { ...entry, accessed_at: new Date().toISOString(), access_count: entry.access_count + 1 };
    this.store.set(entry.id, updated);
    return updated;
  }

  readById(id: string): MemoryEntry | undefined { return this.store.get(id); }

  query(opts: MemoryQueryOptions = {}): MemoryQueryResult {
    let entries = Array.from(this.store.values()).filter(e => !this.isExpired(e));
    if (!opts.include_archived) entries = entries.filter(e => e.status !== "archived");
    if (opts.tier) entries = entries.filter(e => e.tier === opts.tier);
    if (opts.tag) entries = entries.filter(e => e.tags.includes(opts.tag!));
    if (opts.status) entries = entries.filter(e => e.status === opts.status);
    if (opts.session_id) entries = entries.filter(e => e.session_id === opts.session_id);
    if (opts.since) entries = entries.filter(e => e.created_at >= opts.since!);
    entries.sort((a, b) => { const d = TIER_PRIORITY[a.tier] - TIER_PRIORITY[b.tier]; return d !== 0 ? d : b.updated_at.localeCompare(a.updated_at); });
    if (opts.limit) entries = entries.slice(0, opts.limit);
    const tiers = { core: 0, episodic: 0, semantic: 0, working: 0, procedural: 0 } as Record<MemoryTier, number>;
    for (const e of entries) tiers[e.tier]++;
    return { entries, total: entries.length, tiers };
  }

  search(queryText: string, limit = 10): MemoryEntry[] {
    const q = queryText.toLowerCase();
    const entries = Array.from(this.store.values()).filter(e => {
      if (e.status === "archived" || this.isExpired(e)) return false;
      return e.key.toLowerCase().includes(q) || e.summary.toLowerCase().includes(q) || (typeof e.value === "string" && e.value.toLowerCase().includes(q)) || e.tags.some(t => t.toLowerCase().includes(q));
    });
    entries.sort((a, b) => b.access_count - a.access_count);
    return entries.slice(0, limit);
  }

  archive(key: string): boolean {
    const entry = this.getByKey(key);
    if (!entry) return false;
    this.store.set(entry.id, { ...entry, status: "archived", updated_at: new Date().toISOString() });
    return true;
  }

  delete(key: string): boolean {
    const entry = this.getByKey(key);
    if (!entry) return false;
    this.store.delete(entry.id);
    this.keyIndex.delete(key);
    return true;
  }

  clearWorking(sessionId: string): number {
    let cleared = 0;
    for (const [id, entry] of this.store.entries()) {
      if (entry.tier === "working" && entry.session_id === sessionId) {
        this.store.delete(id);
        this.keyIndex.delete(entry.key);
        cleared++;
      }
    }
    return cleared;
  }

  getStats(): MemoryStats {
    const entries = Array.from(this.store.values()).filter(e => !this.isExpired(e));
    const by_tier = { core: 0, episodic: 0, semantic: 0, working: 0, procedural: 0 } as Record<MemoryTier, number>;
    const by_status = { active: 0, archived: 0, pending_review: 0, flagged: 0 } as Record<MemoryStatus, number>;
    let total_access_count = 0, oldest: string | null = null, newest: string | null = null;
    for (const e of entries) {
      by_tier[e.tier]++; by_status[e.status]++; total_access_count += e.access_count;
      if (!oldest || e.created_at < oldest) oldest = e.created_at;
      if (!newest || e.created_at > newest) newest = e.created_at;
    }
    return { total_entries: entries.length, by_tier, by_status, oldest_entry: oldest, newest_entry: newest, total_access_count };
  }

  exportJSON(): string { return JSON.stringify(Array.from(this.store.values()), null, 2); }

  importJSON(json: string): { imported: number; skipped: number } {
    const entries: MemoryEntry[] = JSON.parse(json);
    let imported = 0, skipped = 0;
    for (const entry of entries) {
      if (this.keyIndex.has(entry.key)) { skipped++; continue; }
      this.store.set(entry.id, entry);
      this.keyIndex.set(entry.key, entry.id);
      imported++;
    }
    return { imported, skipped };
  }

  getCount(): number { return this.store.size; }

  private getByKey(key: string): MemoryEntry | undefined {
    const id = this.keyIndex.get(key);
    return id ? this.store.get(id) : undefined;
  }
  private isExpired(entry: MemoryEntry): boolean { return !!entry.ttl && Date.now() > entry.ttl; }
  private expire(id: string): void { const e = this.store.get(id); if (e) { this.store.delete(id); this.keyIndex.delete(e.key); } }
}

export default MemoryStore;
