# LLM Services Infrastructure Index — External Snapshot 2026

**Repo:** `av/awesome-llm-services`  
**Catalog size:** 138+ services  
**Snapshot date:** 2026-06-29  
**Issue:** [#697](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/697)  
**Status:** Architecture reference — catalog for GAIA's model routing and infrastructure decisions

---

## 1. What This Catalog Tells Us

The `av/awesome-llm-services` catalog is a curated index of **138+ self-hostable LLM services, tools, and infrastructure components** for running AI locally. Inclusion criteria: open source and self-hostable. This catalog is the most comprehensive public map of the local-first AI infrastructure ecosystem.

The existence of this catalog — and its 138+ entries — confirms that local-first AI infrastructure is a mature, vibrant ecosystem, not a niche. GAIA's local-first sovereignty principle (ADR-0011) is building on solid, well-populated ground.

---

## 2. Infrastructure Categories Relevant to GAIA

### Model Serving & Runtime
- **Ollama** — the de facto standard for local model serving; the primary GAIA model runtime
- **LMStudio** — desktop GUI for local models; useful reference for UX patterns
- **llama.cpp** — low-level inference backend; relevant for embedded/edge GAIA deployments
- **vLLM** — high-throughput serving for larger local deployments

### API & Routing Layer
- **LocalAI** — OpenAI-compatible API for local models; enables drop-in cloud replacement
- **LiteLLM** — unified API proxy supporting 100+ LLM providers including local; directly relevant for `inference_router.py` design
- **OpenRouter** — routing layer with fallback logic; useful pattern reference for GAIA's sovereignty routing

### RAG & Memory Infrastructure
- **Chroma** — lightweight local vector database; current GAIA candidate
- **Qdrant** — high-performance vector search; production-scale option
- **Weaviate** — knowledge graph + vector hybrid; relevant for GAIA's Akashic memory layer
- **LightRAG** — local RAG pipeline; self-contained

### Agent & Orchestration Infrastructure
- **LangGraph** — (see dedicated snapshot)
- **CrewAI** — (see dedicated snapshot)
- **Haystack** — production-ready RAG and agent pipeline framework
- **AutoGen/AG2** — conversational multi-agent (experimental; not recommended for GAIA production)

### Monitoring & Observability
- **LangFuse** — open-source LLM observability; self-hostable; directly relevant to GAIA's metrics_list.md (#646)
- **Phoenix (Arize)** — LLM tracing and evaluation; open-source
- **AgentOps** — agent-specific observability

---

## 3. Sovereignty Hedge — Infrastructure Implications

The Anthropic access restriction event (June 2026) makes the following infrastructure decisions critical for GAIA:

1. **`inference_router.py` must use LiteLLM or equivalent** as a unified API layer that can swap between Ollama (local) and cloud providers without code changes — sovereignty routing is a config change, not a code change
2. **Ollama is the local runtime** — 138+ catalog entries confirm it is the ecosystem standard
3. **All GAIA dependencies must have self-hostable equivalents** — no single cloud provider can be a hard dependency

---

## 4. Recommended GAIA Infrastructure Stack (from catalog)

| Layer | Recommended | Rationale |
|---|---|---|
| Model serving | **Ollama** | Ecosystem standard, GAIA already uses |
| API routing | **LiteLLM** | Unified local+cloud API; sovereignty routing |
| Vector DB | **Qdrant** (scale) / **Chroma** (dev) | Both self-hostable, open-source |
| Observability | **LangFuse** | Self-hostable, open-source, LLM-native |
| Orchestration | **LangGraph** | (see ADR-0009) |
| Tool interface | **MCP** | (see ADR-0010) |

---

## 5. License & Reuse Posture

The catalog itself is a reference list — MIT. Each cataloged service has its own license. For any service GAIA integrates: verify license before adoption. Ollama (MIT), LiteLLM (MIT), Chroma (Apache 2.0), Qdrant (Apache 2.0), LangFuse (MIT) — all safe for production integration.

---

## Key Takeaways for GAIA

**Adopt:**
- LiteLLM as the unified API routing layer for `inference_router.py` — enables sovereignty routing as a config change
- LangFuse as the self-hostable observability backend for GAIA's metrics layer (#646)
- Qdrant as the production vector database for GAIA's Akashic long-term memory

**Strategic confirmation:**
- Local-first AI infrastructure is a mature ecosystem — GAIA's sovereignty principle is well-supported
- 138+ self-hostable options means GAIA will never be forced to depend on a single cloud provider
