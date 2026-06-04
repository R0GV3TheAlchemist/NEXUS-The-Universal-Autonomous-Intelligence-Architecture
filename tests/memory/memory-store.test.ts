// tests/memory/memory-store.test.ts
// GAIA-OS Memory Layer — Unit Tests
// Issue: #222

import { MemoryStore } from "../../src/memory/memory-store";
import { MemoryManager } from "../../src/memory/memory-manager";
import { bootstrapMemory, GAIA_CORE_IDENTITY } from "../../src/memory/bootstrap";
import { createObservabilityStack } from "../../src/observability/index";

const SESSION = "test-session-memory-001";

describe("MemoryStore", () => {
  let store: MemoryStore;
  beforeEach(() => { store = new MemoryStore(); });

  it("writes and reads a memory entry", () => { store.write("gaian.name", "R0GV3", SESSION, { tier: "core", summary: "Gaian name" }); expect(store.read("gaian.name")?.value).toBe("R0GV3"); });
  it("updates an existing memory on re-write", () => { store.write("k", "v1", SESSION); store.write("k", "v2", SESSION); expect(store.read("k")?.value).toBe("v2"); expect(store.getCount()).toBe(1); });
  it("increments access_count on read", () => { store.write("c", 1, SESSION); store.read("c"); store.read("c"); expect(store.read("c")?.access_count).toBe(3); });
  it("returns undefined for missing key", () => { expect(store.read("nope")).toBeUndefined(); });
  it("archives without deleting", () => { store.write("old", "x", SESSION); store.archive("old"); expect(store.query({ include_archived: true }).entries[0].status).toBe("archived"); expect(store.query({}).entries.length).toBe(0); });
  it("deletes permanently", () => { store.write("t", "v", SESSION); store.delete("t"); expect(store.read("t")).toBeUndefined(); expect(store.getCount()).toBe(0); });
  it("clears working memory for a session", () => { store.write("working.a", 1, SESSION, { tier: "working" }); store.write("working.b", 2, SESSION, { tier: "working" }); store.write("core.x", 3, SESSION, { tier: "core" }); expect(store.clearWorking(SESSION)).toBe(2); expect(store.getCount()).toBe(1); });
  it("searches by text", () => { store.write("crystal.quartz", "amp", SESSION, { summary: "Quartz is a master amplifier crystal" }); store.write("emerald", "asab", SESSION, { summary: "Emerald Tablet" }); expect(store.search("quartz").length).toBe(1); });
  it("queries by tier", () => { store.write("c", 1, SESSION, { tier: "core" }); store.write("s", 2, SESSION, { tier: "semantic" }); expect(store.query({ tier: "core" }).entries.length).toBe(1); });
  it("respects TTL expiry", () => { store.write("exp", "gone", SESSION, { ttl: Date.now() - 1 }); expect(store.read("exp")).toBeUndefined(); });
  it("exports and imports", () => { store.write("e", "hello", SESSION, { summary: "test" }); const s2 = new MemoryStore(); const { imported } = s2.importJSON(store.exportJSON()); expect(imported).toBe(1); expect(s2.read("e")?.value).toBe("hello"); });
  it("computes stats", () => { store.write("c", 1, SESSION, { tier: "core" }); store.write("s", 2, SESSION, { tier: "semantic" }); expect(store.getStats().total_entries).toBe(2); expect(store.getStats().by_tier.core).toBe(1); });
});

describe("MemoryManager", () => {
  let manager: MemoryManager;
  beforeEach(() => { manager = new MemoryManager(new MemoryStore(), createObservabilityStack(SESSION), SESSION); });

  it("remembers and recalls", () => { manager.remember("fact", "GAIA is sovereign", { summary: "sovereignty" }); expect(manager.recall("fact")).toBe("GAIA is sovereign"); });
  it("stores Gaian as core", () => { manager.rememberGaian("R0GV3"); expect(manager.recallEntry("gaian.identity")?.tier).toBe("core"); });
  it("records episodic events", () => { manager.rememberEvent("sprint_1", "Sprint 1 complete"); expect(manager.query({ tier: "episodic" }).length).toBeGreaterThan(0); });
  it("consolidates session and clears working memory", () => {
    manager.setWorkingContext("goal", "build memory");
    manager.consolidateSession({ session_id: SESSION, started_at: new Date().toISOString(), ended_at: new Date().toISOString(), goal: "build memory layer", outcome: "success", key_events: ["shipped"], tools_used: ["github.push_files"], memories_created: 5, memories_updated: 2 });
    expect(manager.recall("working.goal")).toBeNull();
    expect(manager.recallHistory(1)[0].goal).toBe("build memory layer");
  });
  it("searches by text", () => { manager.learn("hermetics", "as above", "The first Hermetic principle"); expect(manager.search("hermetic").length).toBeGreaterThan(0); });
});

describe("bootstrapMemory", () => {
  it("writes core identity on first boot", () => { const s = new MemoryStore(); bootstrapMemory(SESSION, s); expect((s.read("gaia.identity")?.value as any)?.boot_count).toBe(1); });
  it("increments boot_count", () => { const s = new MemoryStore(); bootstrapMemory(SESSION, s); bootstrapMemory(SESSION + "-2", s); expect((s.read("gaia.identity")?.value as any)?.boot_count).toBe(2); });
  it("writes Gaian identity", () => { const s = new MemoryStore(); bootstrapMemory(SESSION, s); expect((s.read("gaian.identity")?.value as any)?.name).toBe(GAIA_CORE_IDENTITY.gaian_name); });
  it("is idempotent", () => { const s = new MemoryStore(); bootstrapMemory(SESSION, s); bootstrapMemory(SESSION, s); bootstrapMemory(SESSION, s); expect(s.query({ tier: "core" }).entries.filter(e => e.key === "gaia.identity").length).toBe(1); });
});
