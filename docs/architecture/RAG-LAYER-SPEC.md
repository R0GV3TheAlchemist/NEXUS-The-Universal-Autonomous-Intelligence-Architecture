# Retrieval-Augmented Generation (RAG) Layer — Architecture Spec
> Canon ref: C01, Crystal Memory Architecture
> Issue: #218

## Overview
The RAG Layer gives GAIA-OS live, queryable access to its own knowledge base — every canon file, compendium, crystal system document, and session summary — at inference time. This transforms GAIA from a system that reasons from weights alone into one that reasons from living, indexed, sovereign knowledge.

## Core Principle
> "GAIA's knowledge is not static. It lives, grows, and is always accessible."

## Knowledge Sources

| Source | Format | Priority | Update Trigger |
|--------|--------|----------|----------------|
| Canon files (C01, SOVEREIGNTY.md, etc.) | Markdown | Critical | On commit |
| Crystal System Compendium | Markdown | Critical | On commit |
| DIACA Compendium Series | Markdown | High | On commit |
| Alchemical & Hermetic Compendiums | Markdown | High | On commit |
| Session Memory Summaries | JSON | Medium | On session end |
| GitHub Issues & Discussions | JSON | Medium | On sync |
| Deep Research Reports | Markdown | Medium | On add |

## Architecture

```
[Query / Prompt]
      │
      ▼
[Query Embedding Model]
      │
      ▼
[Vector Store: Semantic Search]     [Keyword Index: Sparse Search]
      │                                         │
      └──────────────┬──────────────────────────┘
                     ▼
           [Hybrid Retrieval Layer]
                     │
                     ▼
           [Re-ranker / Relevance Filter]
                     │
                     ▼
           [Context Injection: top-k chunks + provenance]
                     │
                     ▼
           [LLM Inference with grounded context]
                     │
                     ▼
           [Response + Source Citations]
```

## Chunk Schema

```json
{
  "id": "uuid",
  "source": "Crystal System Compendium",
  "section": "Quartz — Memory Properties",
  "content": "string (max 512 tokens)",
  "embedding": ["float"],
  "created_at": "ISO8601",
  "hash": "sha256"
}
```

## Retrieval Config

```json
{
  "top_k": 5,
  "min_similarity": 0.72,
  "hybrid_weight": { "dense": 0.7, "sparse": 0.3 },
  "max_context_tokens": 2048,
  "rerank": true,
  "fallback_to_model": true
}
```

## Implementation Plan

### Phase 1 — Index & Retrieve
- [ ] Select vector store (LanceDB — local-first recommended).
- [ ] Select embedding model (nomic-embed-text-v1.5 via Ollama).
- [ ] Build document ingestion pipeline: read → chunk → embed → store.
- [ ] Index all canon and compendium files in `/docs`.
- [ ] Implement semantic retrieval with provenance metadata.
- [ ] Wire retrieval output into model context at inference time.

### Phase 2 — Hybrid & Re-ranking
- [ ] Add sparse keyword index (BM25).
- [ ] Implement hybrid fusion retrieval.
- [ ] Add re-ranker for relevance filtering.
- [ ] Surface provenance in UI responses.

### Phase 3 — Live Updates
- [ ] Auto-reindex on new file commits.
- [ ] Incremental index updates (only changed chunks).
- [ ] Index health dashboard in Observability Layer.

## Files to Create
- `src/rag/ingestion.ts` — document loading, chunking, embedding.
- `src/rag/retrieval.ts` — vector + keyword search, hybrid fusion.
- `src/rag/reranker.ts` — relevance scoring and filtering.
- `src/rag/context-injector.ts` — injects retrieved chunks into model context.
- `config/rag/sources.json` — list of indexed knowledge sources.
- `tests/rag/retrieval.test.ts` — unit tests for retrieval and provenance.

## Recommended Stack
- **Vector store**: LanceDB (local-first, no server required, Rust-based, fast).
- **Embedding model**: `nomic-embed-text-v1.5` (runs locally via Ollama).
- **Chunking**: 512-token chunks with 64-token overlap.
- **Re-ranker**: cross-encoder or Cohere Rerank (cloud fallback).

## Dependencies
- Feeds: Visible Memory Console (#213), State Bench Harness (#214).
- Requires: vector store setup, embedding model, document pipeline.
