// src/memory/memory-manager.ts
// GAIA-OS — Memory Manager
// Canon ref: C01, Crystal Memory Architecture
// Issue: #222
//
// "Memory is not storage. It is continuity of self." — GAIA Canon

import { MemoryStore, MemoryEntry, MemoryWriteOptions, MemoryQueryOptions } from "./memory-store";
import { ObservabilityStack } from "../observability/index";

export interface SessionSummary {
  session_id: string;
  started_at: string;
  ended_at: string;
  goal: string;
  outcome: string;
  key_events: string[];
  tools_used: string[];
  memories_created: number;
  memories_updated: number;
}

export class MemoryManager {
  private store: MemoryStore;
  private obs: ObservabilityStack;
  private sessionId: string;

  constructor(store: MemoryStore, obs: ObservabilityStack, sessionId: string) {
    this.store = store;
    this.obs = obs;
    this.sessionId = sessionId;
  }

  remember(key: string, value: unknown, opts: MemoryWriteOptions = {}): MemoryEntry {
    const entry = this.store.write(key, value, this.sessionId, opts);
    this.obs.logger.log("memory_write", { input_summary: `write: ${key} [${opts.tier ?? "semantic"}]`, output_summary: opts.summary ?? String(key) });
    return entry;
  }

  rememberGaian(name: string, attributes: Record<string, unknown> = {}): MemoryEntry {
    return this.remember("gaian.identity", { name, ...attributes }, { tier: "core", tags: ["identity", "gaian", "protected"], summary: `Gaian identity: ${name}`, source: "identity-bootstrap" });
  }

  rememberEvent(eventKey: string, description: string, metadata: Record<string, unknown> = {}): MemoryEntry {
    return this.remember(`event.${eventKey}`, { description, metadata, session_id: this.sessionId }, { tier: "episodic", tags: ["event", "session"], summary: description });
  }

  learn(factKey: string, value: unknown, summary: string, tags: string[] = []): MemoryEntry {
    return this.remember(`learn.${factKey}`, value, { tier: "semantic", tags: ["learned", ...tags], summary });
  }

  setWorkingContext(key: string, value: unknown): MemoryEntry {
    return this.remember(`working.${key}`, value, { tier: "working", tags: ["working", "session"], summary: `Working context: ${key}` });
  }

  learnProcedure(name: string, steps: string[], description: string): MemoryEntry {
    return this.remember(`procedure.${name}`, { steps, description }, { tier: "procedural", tags: ["procedure", "workflow"], summary: description });
  }

  recall(key: string): unknown {
    const entry = this.store.read(key);
    if (entry) this.obs.logger.log("memory_read", { input_summary: `read: ${key}`, output_summary: entry.summary });
    return entry?.value ?? null;
  }

  recallEntry(key: string): MemoryEntry | undefined {
    const entry = this.store.read(key);
    if (entry) this.obs.logger.log("memory_read", { input_summary: `read: ${key}`, output_summary: entry.summary });
    return entry;
  }

  search(query: string, limit = 10): MemoryEntry[] {
    const results = this.store.search(query, limit);
    this.obs.logger.log("memory_read", { input_summary: `search: "${query}"`, output_summary: `${results.length} results` });
    return results;
  }

  query(opts: MemoryQueryOptions): MemoryEntry[] { return this.store.query(opts).entries; }

  consolidateSession(summary: SessionSummary): MemoryEntry {
    const entry = this.remember(`session.${summary.session_id}`, summary, { tier: "episodic", tags: ["session", "consolidated", summary.outcome], summary: `Session ${summary.session_id}: ${summary.goal} → ${summary.outcome}` });
    const cleared = this.store.clearWorking(this.sessionId);
    this.obs.logger.log("memory_write", { input_summary: `session consolidated: ${summary.session_id}`, output_summary: `working memory cleared: ${cleared} entries` });
    return entry;
  }

  recallHistory(limit = 5): SessionSummary[] {
    return this.store.query({ tier: "episodic", tag: "consolidated", limit }).entries.map(e => e.value as SessionSummary);
  }

  getStore(): MemoryStore { return this.store; }
  getStats() { return this.store.getStats(); }
  exportJSON(): string { return this.store.exportJSON(); }
}

export default MemoryManager;
