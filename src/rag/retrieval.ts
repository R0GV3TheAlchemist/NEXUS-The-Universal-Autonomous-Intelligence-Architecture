// src/rag/retrieval.ts
// GAIA-OS RAG Layer — Hybrid Retrieval Engine
// Canon ref: C01, Crystal Memory Architecture
// Issue: #218

import { DocumentChunk } from "./ingestion";

export interface RetrievalQuery {
  text: string;
  top_k?: number;
  min_similarity?: number;
  source_filter?: string[];
}

export interface RetrievedChunk {
  chunk: DocumentChunk;
  score: number;
  dense_score: number;
  sparse_score: number;
  rank: number;
}

export interface RetrievalResult {
  query: string;
  chunks: RetrievedChunk[];
  retrieval_ms: number;
  fallback: boolean;
}

export const RETRIEVAL_CONFIG = {
  top_k: 5,
  min_similarity: 0.72,
  hybrid_weight: { dense: 0.7, sparse: 0.3 },
  max_context_tokens: 2048,
  rerank: true,
} as const;

export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) return 0;
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; normA += a[i] * a[i]; normB += b[i] * b[i]; }
  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  return denom === 0 ? 0 : dot / denom;
}

export function tokenize(text: string): string[] {
  return text.toLowerCase().replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter(Boolean);
}

export function bm25Score(queryTokens: string[], docTokens: string[], avgDocLength: number, k1 = 1.5, b = 0.75): number {
  const docLen = docTokens.length;
  const tf: Record<string, number> = {};
  for (const t of docTokens) tf[t] = (tf[t] ?? 0) + 1;
  let score = 0;
  for (const qt of queryTokens) {
    const tfScore = tf[qt] ?? 0;
    if (tfScore === 0) continue;
    score += (tfScore * (k1 + 1)) / (tfScore + k1 * (1 - b + b * (docLen / avgDocLength)));
  }
  return score;
}

export class RetrievalEngine {
  private chunks: DocumentChunk[] = [];
  private avgDocLength = 0;

  loadChunks(chunks: DocumentChunk[]): void {
    this.chunks = chunks;
    const totalTokens = chunks.reduce((sum, c) => sum + c.token_count, 0);
    this.avgDocLength = chunks.length > 0 ? totalTokens / chunks.length : 1;
  }

  retrieve(queryEmbedding: number[] | null, query: RetrievalQuery): RetrievalResult {
    const start = Date.now();
    const config = { ...RETRIEVAL_CONFIG, ...query };
    const queryTokens = tokenize(query.text);
    let candidates = this.chunks;
    if (query.source_filter?.length) candidates = candidates.filter(c => query.source_filter!.includes(c.source_id));

    const scored = candidates.map(chunk => {
      const dense_score = (queryEmbedding && chunk.embedding) ? cosineSimilarity(queryEmbedding, chunk.embedding) : 0;
      const docTokens = tokenize(chunk.content);
      const sparse_score = Math.min(bm25Score(queryTokens, docTokens, this.avgDocLength) / 10, 1);
      const w = RETRIEVAL_CONFIG.hybrid_weight;
      const score = queryEmbedding ? w.dense * dense_score + w.sparse * sparse_score : sparse_score;
      return { chunk, score, dense_score, sparse_score, rank: 0 };
    });

    scored.sort((a, b) => b.score - a.score);
    const filtered = scored.filter(r => r.score >= config.min_similarity);
    const fallback = filtered.length === 0;
    const topK = (fallback ? scored : filtered).slice(0, config.top_k);
    topK.forEach((r, i) => { r.rank = i + 1; });
    return { query: query.text, chunks: topK, retrieval_ms: Date.now() - start, fallback };
  }

  getChunkCount(): number { return this.chunks.length; }
}

export default RetrievalEngine;
