// src/rag/context-injector.ts
// GAIA-OS RAG Layer — Context Injector
// Canon ref: C01
// Issue: #218

import { RetrievedChunk } from "./retrieval";
import { INGESTION_CONFIG } from "./ingestion";

export interface InjectedContext {
  context_block: string;
  sources: SourceCitation[];
  total_tokens: number;
  chunk_count: number;
  truncated: boolean;
}

export interface SourceCitation {
  rank: number;
  source_label: string;
  section: string;
  score: number;
  source_id: string;
}

export const INJECTION_CONFIG = {
  max_context_tokens: 2048,
  context_header: "## GAIA Knowledge Context\n> The following is retrieved from GAIA's sovereign knowledge base.\n",
  citation_footer: "\n---\n**Sources used in this response:**",
} as const;

export function buildContextBlock(chunks: RetrievedChunk[], maxTokens = INJECTION_CONFIG.max_context_tokens): InjectedContext {
  const sources: SourceCitation[] = [];
  const parts: string[] = [INJECTION_CONFIG.context_header];
  let totalTokens = Math.ceil(INJECTION_CONFIG.context_header.length / INGESTION_CONFIG.chars_per_token);
  let truncated = false;

  for (const result of chunks) {
    const { chunk, score, rank } = result;
    const block = `\n### [${rank}] ${chunk.source_label} — ${chunk.section}\n${chunk.content}\n`;
    const blockTokens = Math.ceil(block.length / INGESTION_CONFIG.chars_per_token);
    if (totalTokens + blockTokens > maxTokens) { truncated = true; break; }
    parts.push(block);
    totalTokens += blockTokens;
    sources.push({ rank, source_label: chunk.source_label, section: chunk.section, score: Math.round(score * 100) / 100, source_id: chunk.source_id });
  }

  return { context_block: parts.join(""), sources, total_tokens: totalTokens, chunk_count: sources.length, truncated };
}

export function buildCitationFooter(sources: SourceCitation[]): string {
  if (sources.length === 0) return "";
  const lines = sources.map(s => `[${s.rank}] **${s.source_label}** — *${s.section}* (relevance: ${(s.score * 100).toFixed(0)}%)`);
  return `${INJECTION_CONFIG.citation_footer}\n${lines.join("\n")}`;
}

export default { buildContextBlock, buildCitationFooter };
