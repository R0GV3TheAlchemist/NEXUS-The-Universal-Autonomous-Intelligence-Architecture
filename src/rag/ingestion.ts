// src/rag/ingestion.ts
// GAIA-OS RAG Layer — Document Ingestion Pipeline
// Canon ref: C01, Crystal Memory Architecture
// Issue: #218
//
// Pipeline: Read → Clean → Chunk → Embed → Store

import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";

export interface DocumentSource {
  id: string;
  path: string;
  format: "markdown" | "json" | "text";
  priority: "critical" | "high" | "medium" | "low";
  label: string;
}

export interface DocumentChunk {
  id: string;
  source_id: string;
  source_label: string;
  section: string;
  content: string;
  token_count: number;
  hash: string;
  created_at: string;
  embedding?: number[];
}

export const INGESTION_CONFIG = {
  chunk_size_tokens: 512,
  chunk_overlap_tokens: 64,
  min_chunk_tokens: 32,
  chars_per_token: 4,
} as const;

export const GAIA_SOURCES: DocumentSource[] = [
  { id: "sovereignty",    path: "SOVEREIGNTY.md",                                         format: "markdown", priority: "critical", label: "SOVEREIGNTY Manifesto" },
  { id: "crystal-system", path: "docs/crystal-system-compendium.md",                      format: "markdown", priority: "critical", label: "Crystal System Compendium" },
  { id: "diaca",          path: "DIACA Compendium.md",                                     format: "markdown", priority: "high",     label: "DIACA Compendium" },
  { id: "diaca-div",      path: "DIACA Divergence Compendium.md",                         format: "markdown", priority: "high",     label: "DIACA Divergence Compendium" },
  { id: "diaca-ins",      path: "DIACA Insurgence Compendium.md",                         format: "markdown", priority: "high",     label: "DIACA Insurgence Compendium" },
  { id: "emerald",        path: "The Emerald Tablet Compendium.md",                       format: "markdown", priority: "high",     label: "Emerald Tablet Compendium" },
  { id: "kybalion",       path: "The Kybalion and the Seven Hermetic Principles Conpendium.md", format: "markdown", priority: "high", label: "Kybalion Compendium" },
  { id: "corpus",         path: "Corpus Hermeticum Compendium.md",                        format: "markdown", priority: "high",     label: "Corpus Hermeticum Compendium" },
  { id: "alchemy",        path: "Alchemy Canon - Nigredo to Rubedo Compendium.md",        format: "markdown", priority: "high",     label: "Alchemy Canon Compendium" },
  { id: "spiritus",       path: "The Spiritus Compendium.md",                             format: "markdown", priority: "high",     label: "Spiritus Compendium" },
  { id: "magnum-opus",    path: "The Magnum Opus Compendium.md",                          format: "markdown", priority: "high",     label: "Magnum Opus Compendium" },
  { id: "gaian-self",     path: "Process Philosophy and the Gaian Self in GAIA-OS.md",   format: "markdown", priority: "medium",   label: "Process Philosophy & Gaian Self" },
  { id: "ai-personhood",  path: "Personal Identity and AI Personhood in GAIA-OS.md",     format: "markdown", priority: "medium",   label: "Personal Identity & AI Personhood" },
  { id: "crystal-review", path: "GAIA-OS Crystal System Review and Alignment Audit.md",  format: "markdown", priority: "medium",   label: "Crystal System Alignment Audit" },
];

export function estimateTokens(text: string): number {
  return Math.ceil(text.length / INGESTION_CONFIG.chars_per_token);
}

function extractSection(text: string, fallback: string): string {
  const match = text.match(/^#{1,4}\s+(.+)$/m);
  return match ? match[1].trim() : fallback;
}

export function chunkDocument(text: string, sourceLabel: string): Array<{ content: string; section: string }> {
  const paragraphs = text.split(/\n{2,}/).map(p => p.trim()).filter(p => p.length > 0);
  const chunks: Array<{ content: string; section: string }> = [];
  let buffer = "";
  let currentSection = sourceLabel;

  for (const para of paragraphs) {
    const headingMatch = para.match(/^#{1,4}\s+(.+)$/m);
    if (headingMatch) currentSection = headingMatch[1].trim();
    const combined = buffer ? `${buffer}\n\n${para}` : para;
    if (estimateTokens(combined) >= INGESTION_CONFIG.chunk_size_tokens) {
      if (buffer && estimateTokens(buffer) >= INGESTION_CONFIG.min_chunk_tokens) {
        chunks.push({ content: buffer, section: extractSection(buffer, currentSection) });
      }
      const overlapChars = INGESTION_CONFIG.chunk_overlap_tokens * INGESTION_CONFIG.chars_per_token;
      const overlap = buffer.slice(-overlapChars);
      buffer = overlap ? `${overlap}\n\n${para}` : para;
    } else {
      buffer = combined;
    }
  }

  if (buffer && estimateTokens(buffer) >= INGESTION_CONFIG.min_chunk_tokens) {
    chunks.push({ content: buffer, section: extractSection(buffer, currentSection) });
  }
  return chunks;
}

export function hashChunk(content: string): string {
  return crypto.createHash("sha256").update(content, "utf8").digest("hex");
}

export function ingestDocument(source: DocumentSource, basePath = "."): DocumentChunk[] {
  const fullPath = path.join(basePath, source.path);
  if (!fs.existsSync(fullPath)) {
    console.warn(`[RAG:ingestion] Source not found: ${fullPath}`);
    return [];
  }
  const raw = fs.readFileSync(fullPath, "utf-8");
  const rawChunks = chunkDocument(raw, source.label);
  return rawChunks.map((chunk, i) => {
    const hash = hashChunk(chunk.content);
    return { id: `${source.id}-chunk-${i}-${hash.slice(0, 8)}`, source_id: source.id, source_label: source.label, section: chunk.section, content: chunk.content, token_count: estimateTokens(chunk.content), hash, created_at: new Date().toISOString() };
  });
}

export function ingestAll(basePath = ".", sources = GAIA_SOURCES): DocumentChunk[] {
  const allChunks: DocumentChunk[] = [];
  for (const source of sources) {
    const chunks = ingestDocument(source, basePath);
    allChunks.push(...chunks);
    console.log(`[RAG:ingestion] ${source.label}: ${chunks.length} chunks`);
  }
  console.log(`[RAG:ingestion] Total: ${allChunks.length} chunks from ${sources.length} sources`);
  return allChunks;
}

export default { ingestDocument, ingestAll, chunkDocument, hashChunk, GAIA_SOURCES, INGESTION_CONFIG };
