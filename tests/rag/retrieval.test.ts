// tests/rag/retrieval.test.ts
// GAIA-OS RAG Layer — Unit Tests
// Issue: #218

import { RetrievalEngine, cosineSimilarity, bm25Score, tokenize } from "../../src/rag/retrieval";
import { chunkDocument, hashChunk, estimateTokens } from "../../src/rag/ingestion";
import { buildContextBlock, buildCitationFooter } from "../../src/rag/context-injector";
import type { DocumentChunk } from "../../src/rag/ingestion";

function makeChunk(overrides: Partial<DocumentChunk> = {}): DocumentChunk {
  return { id: "test-chunk-001", source_id: "crystal-system", source_label: "Crystal System Compendium", section: "Quartz Properties", content: "Quartz is a master amplifier crystal used for memory and clarity in GAIA-OS.", token_count: 18, hash: "abc123", created_at: new Date().toISOString(), embedding: [0.1, 0.8, 0.3, 0.5], ...overrides };
}

describe("chunkDocument", () => {
  it("splits a multi-paragraph document into chunks", () => {
    const doc = Array(20).fill("This is a paragraph about crystals and GAIA memory.").join("\n\n");
    const chunks = chunkDocument(doc, "Test Source");
    expect(chunks.length).toBeGreaterThan(1);
  });
  it("returns a single chunk for a short document", () => {
    expect(chunkDocument("Short doc.", "Src").length).toBe(1);
  });
  it("extracts markdown headings as section names", () => {
    const chunks = chunkDocument("## Crystal Memory\n\nQuartz amplifies memory.", "Src");
    expect(chunks[0].section).toBe("Crystal Memory");
  });
});

describe("hashChunk", () => {
  it("is deterministic", () => { expect(hashChunk("hello")).toBe(hashChunk("hello")); });
  it("differs for different content", () => { expect(hashChunk("a")).not.toBe(hashChunk("b")); });
});

describe("cosineSimilarity", () => {
  it("returns 1 for identical vectors", () => { expect(cosineSimilarity([1,0],[1,0])).toBeCloseTo(1); });
  it("returns 0 for orthogonal vectors", () => { expect(cosineSimilarity([1,0],[0,1])).toBeCloseTo(0); });
  it("returns 0 for mismatched lengths", () => { expect(cosineSimilarity([1,2],[1,2,3])).toBe(0); });
});

describe("bm25Score", () => {
  it("scores higher for more query term matches", () => {
    const q = tokenize("crystal memory gaia");
    expect(bm25Score(q, tokenize("crystal memory gaia crystal"), 5)).toBeGreaterThan(bm25Score(q, tokenize("unrelated content"), 5));
  });
});

describe("RetrievalEngine", () => {
  let engine: RetrievalEngine;
  beforeEach(() => {
    engine = new RetrievalEngine();
    engine.loadChunks([
      makeChunk({ id: "c1", content: "Quartz amplifies crystal memory.", embedding: [0.9,0.1,0.1,0.1], token_count: 8 }),
      makeChunk({ id: "c2", content: "The Emerald Tablet: as above so below.", embedding: [0.1,0.9,0.1,0.1], token_count: 8 }),
      makeChunk({ id: "c3", content: "GAIA sovereignty requires user control.", embedding: [0.1,0.1,0.9,0.1], token_count: 8 }),
    ]);
  });
  it("returns top-k results", () => { expect(engine.retrieve(null, { text: "crystal", top_k: 2, min_similarity: 0 }).chunks.length).toBeLessThanOrEqual(2); });
  it("sets fallback=true when no results meet min_similarity", () => { expect(engine.retrieve(null, { text: "xyz", top_k: 3, min_similarity: 0.99 }).fallback).toBe(true); });
  it("assigns ascending ranks", () => { engine.retrieve(null, { text: "GAIA", top_k: 3, min_similarity: 0 }).chunks.forEach((r,i) => expect(r.rank).toBe(i+1)); });
});

describe("buildContextBlock", () => {
  it("builds context with citations", () => {
    const ctx = buildContextBlock([{ chunk: makeChunk(), score: 0.9, dense_score: 0.9, sparse_score: 0.8, rank: 1 }]);
    expect(ctx.context_block).toContain("GAIA Knowledge Context");
    expect(ctx.sources.length).toBe(1);
  });
  it("truncates when over token budget", () => {
    const chunks = Array(20).fill(null).map((_,i) => ({ chunk: makeChunk({ id: `c${i}`, content: "x".repeat(2000) }), score: 0.9, dense_score: 0.9, sparse_score: 0.8, rank: i+1 }));
    expect(buildContextBlock(chunks, 512).truncated).toBe(true);
  });
});

describe("buildCitationFooter", () => {
  it("formats sources correctly", () => { expect(buildCitationFooter([{ rank: 1, source_label: "Crystal System", section: "Quartz", score: 0.95, source_id: "cs" }])).toContain("95%"); });
  it("returns empty for no sources", () => { expect(buildCitationFooter([])).toBe(""); });
});
