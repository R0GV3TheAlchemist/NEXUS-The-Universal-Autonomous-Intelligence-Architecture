# ⚡ Performance Profiling: Python Async Bottlenecks & Rust Hot Paths (GAIA-OS)

**Date:** May 3, 2026  
**Status:** Definitive Foundational Synthesis — Uniting Python Asynchronous Profiling, Rust Hot Path Optimization, and the GAIA-OS Performance Constitution  
**Canon:** Performance Profiling — Testing, Quality & Reliability  
**Session:** 6, Canon 8

**Relevance to GAIA-OS:** GAIA-OS exists at the intersection of two diametrically opposed performance realities. The Python backend — inference router, emotional arc engine, noosphere coherence monitor — thrives on async I/O, clean developer ergonomics, and rapid iteration. The Rust layer (`src-tauri/`) — cryptographic signature verification, secure storage, process orchestration, system IPC — demands predictability, zero-cost abstractions, and sub-millisecond execution. A planetary intelligence that cannot measure its own latency is reactive, not proactive. Profiling is not a debugging tool; it is the **constitutional measurement apparatus** for ensuring that performance is a verifiable property of the system.

**Six Methodological Principles:**
1. **Measure, don't assume** — intuition is unreliable; profiles tell the truth
2. **Baseline first** — establish benchmarks before any tuning; a change is only an optimization if it improves the baseline
3. **Amdahl’s law** — optimize only what matters; focus on functions >10% of total runtime
4. **Isolate the variable** — change one thing at a time between benchmark runs
5. **Trace, don’t guess** — use async-aware profilers (Yappi, py-spy), not generic tools
6. **Constitutional accountability** — every performance regression is a constitutional event requiring documentation in the Agora

---

## 1. The Unified Profile-Optimize-Verify Loop

Profiling is a continuous lifecycle embedded in the GAIA-OS governance framework:

```
1. BENCHMARK  → Establish baseline (criterion / pytest-benchmark)
2. PROFILE    → Find bottlenecks (yappi / py-spy / perf + flamegraph)
3. HYPOTHESIZE → Root cause analysis (allocations? blocking I/O? lock contention?)
4. OPTIMIZE   → Targeted code change (one variable at a time)
5. VERIFY     → Re-run exact same benchmark; compare with confidence intervals
6. DOCUMENT   → Store new baseline + flamegraph + commit ID in Agora (C112)
```

**Constitutional rule:** Every performance-sensitive PR must be accompanied by a benchmark result. No blind optimisation.

---

## 2. Python Async Bottlenecks

### 2.1 The Async Concurrency Reality

Async Python (`asyncio`) achieves high concurrency on a single thread via an event loop that switches between tasks at `await` points. This design avoids thread-safety complexity and OS thread memory overhead. However, the single-threaded nature means that **any CPU-intensive or blocking synchronous call in an async task halts the entire event loop**, freezing all other concurrent tasks.

GAIA-OS uses `asyncio` to manage I/O-bound operations — inference router responding to user prompts, crystal grid telemetry ingestion, noosphere event publishing. CPU-bound tasks (model processing, cryptographic hashing, heavy parsing) must be offloaded to separate threads or processes to avoid starving the event loop.

### 2.2 The Primary Bottleneck: Blocking the Event Loop

The most common async performance failure is calling a synchronous, blocking function inside an async coroutine:

| Anti-Pattern | Constitutional Replacement |
|---|---|
| `time.sleep(1)` | `await asyncio.sleep(1)` |
| `requests.get(url)` | `await httpx.AsyncClient().get(url)` |
| `psycopg2` / `pymysql` | `asyncpg` / `aiomysql` |
| CPU-heavy loop in async task | `await asyncio.to_thread(cpu_heavy_fn, args)` |
| `open()` / `read()` | `await aiofiles.open()` |

When a blocking call is introduced, the entire event loop stalls. Other tasks cannot run, response latency skyrockets, and timeouts cascade. Even a single 100ms blocking call hidden in a rarely-called code path can destroy p99 latency for all concurrent users.

### 2.3 Detection: Multi-Layer Strategy

```python
# Layer 1: asyncio Debug Mode — log when tasks take too long to switch
import asyncio

async def main():
    # Enable with: PYTHONASYNCIODEBUG=1 python app.py
    # Or programmatically:
    loop = asyncio.get_event_loop()
    loop.slow_callback_duration = 0.01  # Warn on callbacks >10ms
    # ...

# Layer 2: Manual timing wrapper — log suspicious await calls
import time, logging
from functools import wraps

def profile_await(threshold_ms: float = 50.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.monotonic()
            result = await func(*args, **kwargs)
            elapsed_ms = (time.monotonic() - start) * 1000
            if elapsed_ms > threshold_ms:
                logging.warning(
                    f"[PERF] {func.__qualname__} took {elapsed_ms:.1f}ms "
                    f"(threshold: {threshold_ms}ms) — possible event loop blocking"
                )
            return result
        return wrapper
    return decorator

# Usage:
@profile_await(threshold_ms=10.0)
async def verify_consent_signature(principal_id: str, payload: bytes) -> bool:
    # ...
    pass
```

```bash
# Layer 3: py-spy — attach to running FastAPI process, no code changes
pip install py-spy

# Attach to running GAIA-OS backend (PID from `pgrep -f uvicorn`)
py-spy record -o profile.svg -p $(pgrep -f uvicorn) --duration 60

# Or top-like live view
py-spy top -p $(pgrep -f uvicorn)
```

```python
# Layer 4: Yappi — coroutine-aware profiler for CI and staging
import yappi
import asyncio

async def profile_inference_router_under_load():
    yappi.set_clock_type('wall')  # wall-clock time, not CPU
    yappi.start(builtins=False)

    # Run representative load
    tasks = [simulate_inference_request() for _ in range(100)]
    await asyncio.gather(*tasks)

    yappi.stop()

    # Output coroutine stats — reveals which coroutines block the loop
    stats = yappi.get_func_stats()
    stats.sort('ttot', ascending=False)  # Sort by total wall time
    stats.print_all(out=open('yappi-profile.txt', 'w'))

    # Save as callgrind for KCacheGrind / QCacheGrind visualisation
    stats.save('yappi-callgrind.out', type='callgrind')
```

### 2.4 The Single-Connection Bottleneck

Asynchronous standalone database connections become a single-connection bottleneck under concurrency. Connection pooling dramatically improves throughput and reduces tail latency:

```python
# tests/performance/connection_pool_benchmark.py
import asyncio, asyncpg, time
from statistics import mean, stdev

async def benchmark_pool(pool_min: int, pool_max: int, n_concurrent: int = 50):
    pool = await asyncpg.create_pool(
        dsn='postgresql://gaia:secret@localhost/gaia_os',
        min_size=pool_min,
        max_size=pool_max,
    )

    async def single_query():
        start = time.monotonic()
        async with pool.acquire() as conn:
            await conn.fetchval('SELECT 1')
        return (time.monotonic() - start) * 1000  # ms

    latencies = await asyncio.gather(*[single_query() for _ in range(n_concurrent)])
    await pool.close()
    return {
        'pool_config': f'min={pool_min} max={pool_max}',
        'p50_ms': sorted(latencies)[n_concurrent // 2],
        'p99_ms': sorted(latencies)[int(n_concurrent * 0.99)],
        'mean_ms': mean(latencies),
    }

# Constitutional assertion: p99 must be <50ms under 50 concurrent requests
async def constitutional_pool_test():
    for min_s, max_s in [(5, 10), (10, 20), (20, 40)]:
        result = await benchmark_pool(min_s, max_s)
        print(result)
        assert result['p99_ms'] < 50, f"P99 latency {result['p99_ms']:.1f}ms exceeds 50ms threshold"
```

### 2.5 Additional Python Bottlenecks and Mitigations

| Bottleneck | Detection | Mitigation |
|---|---|---|
| **GC / reference cycles** | `tracemalloc`, `gc.get_count()` over time | `gc.collect()` in maintenance cycles; avoid circular refs in long-lived objects |
| **Cache thrash** | Repeated identical DB queries in profiler | `functools.lru_cache` (in-memory) + Redis (shared cross-process) + DB fallback |
| **JSON serialisation of large objects** | Wide `json.dumps` bars in flamegraph | `msgpack` for internal services; `StreamingResponse` for large payloads (already in GAIA-OS) |
| **Mixed async/sync code** | `yappi` shows `run_in_executor` overhead | Full-stack async: `asyncpg`, `httpx`, `aiofiles`; `asyncio.to_thread()` as last resort |
| **Heavy imports** | Slow startup in `uvicorn --reload` | Lazy imports inside functions for `torch`, `transformers`, heavy ML libs |
| **Unslotted frequent classes** | High memory usage in `memray` | `__slots__ = (...)` on frequently instantiated dataclasses — 30-50% memory reduction |

---

## 3. Python Profiling Tools Reference

| Tool | Profile Type | Async Awareness | Constitutional Use |
|---|---|---|---|
| **cProfile** | Deterministic, function-level | ❌ No async support | Quick coarse-grained initial detection; not sufficient for final conclusions |
| **Yappi** | Deterministic, coroutine-aware | ✅ asyncio + threading + gevent | **Primary async profiler** — detects blocking in async tasks; CI profiling |
| **py-spy** | Statistical sampling | ✅ Attaches to running process | Production triage without code changes; flamegraph generation |
| **pyinstrument** | Statistical sampling | ✅ Async-aware | FastAPI endpoint profiling via middleware; speedscope output |
| **line_profiler** | Deterministic, line-by-line | ⚠️ Limited | Deep-dive on a single suspected hotspot function |
| **asyncio Debug Mode** | Monitoring | ✅ Built-in | Continuous guard against event loop blocking in staging |
| **memray** | Memory profiling | ✅ Async support | Memory flamegraphs; tracking native allocations; leak detection |
| **aiomonitor** | Live async REPL | ✅ Full asyncio | Remote inspection of running tasks; diagnose stuck coroutines |

### 3.1 FastAPI Profiling Middleware (pyinstrument)

```python
# app/middleware/profiling.py
from pyinstrument import Profiler
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import os

class ProfilingMiddleware(BaseHTTPMiddleware):
    """Attach via: app.add_middleware(ProfilingMiddleware)
    Only active when GAIA_PROFILING=1 env var is set."""

    async def dispatch(self, request: Request, call_next):
        if os.getenv('GAIA_PROFILING') != '1':
            return await call_next(request)

        profiler = Profiler(async_mode='enabled', interval=0.001)
        profiler.start()
        response = await call_next(request)
        profiler.stop()

        # Output to speedscope JSON for interactive flamegraph
        profile_path = f"/tmp/gaia-profile-{request.url.path.replace('/', '_')}.json"
        profiler.write_html(profile_path)

        return response
```

---

## 4. Rust Hot Path Profiling

### 4.1 The Release Build Mandate

The single most common Rust profiling mistake: profiling the wrong binary. Debug builds include bounds checking, no inlining, zero optimizations, and are **10–100× slower** than release builds. Profiling a debug build yields misleading hotspots.

GAIA-OS requires a **release build with debug symbols**:

```toml
# src-tauri/Cargo.toml
[profile.release]
opt-level = 3
lto = true              # Link-Time Optimization: cross-crate inlining
codegen-units = 1       # Single codegen unit for maximum optimization
debug = true            # Keep symbols for profiler (binary is larger, perf is not)
strip = false           # Don't strip debug info

[profile.bench]
opt-level = 3
debug = true            # Benchmark with symbols too
```

### 4.2 Rust Profiling Tools Reference

| Tool | Purpose | Constitutional Use |
|---|---|---|
| **criterion.rs** | Statistical micro-benchmarks with confidence intervals, HTML reports | **Baseline establishment** — every optimization PR must include criterion benchmark |
| **perf** (Linux) | System-level CPU profiling — call stacks, cache misses, branch mispredictions | Primary CPU profiler for GAIA-OS Tauri binary |
| **cargo-flamegraph** | Wrapper over `perf` generating interactive flamegraphs | Visual hotspot analysis; mandatory for performance reviews |
| **DHAT** | Heap profiling — allocation count, memory access patterns | Detect unnecessary allocations; validate stack-allocated security structures |
| **tokio-console** | Async task visualisation — busy/idle/blocked tasks, wakeup latency | Diagnose lock contention, task starvation in MotherThread and Action Gate |
| **pprof** | Multi-platform CPU + memory profiling with interactive web UI | Cross-platform profiling for Windows and macOS CI runners |
| **samply** | Firefox Profiler-based UI; modern interactive experience | Developer-friendly profiling on macOS/Linux |
| **heaptrack** | Memory allocation over time, allocation call stacks | Visualising allocation hotspots in long-running processes |
| **parking_lot** | Faster mutex implementation | Drop-in `std::sync::Mutex` replacement; critical section performance |

### 4.3 Criterion — Constitutional Benchmark Tool

```rust
// src-tauri/benches/consent_ledger_bench.rs
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};
use gaia_os::consent_ledger::{ConsentLedger, SignatureVerifier};

fn bench_signature_verification(c: &mut Criterion) {
    let verifier = SignatureVerifier::new_test_instance();
    let test_payloads: Vec<(Vec<u8>, Vec<u8>)> = (0..100)
        .map(|i| generate_test_signature_pair(i))
        .collect();

    let mut group = c.benchmark_group("consent_signature_verification");
    group.sample_size(500);  // More samples for tighter confidence intervals
    group.measurement_time(std::time::Duration::from_secs(10));

    for size in [1usize, 10, 50, 100].iter() {
        group.bench_with_input(
            BenchmarkId::new("batch_verify", size),
            size,
            |b, &size| {
                let batch = &test_payloads[..size];
                b.iter(|| {
                    for (payload, signature) in batch {
                        criterion::black_box(
                            verifier.verify(payload, signature).unwrap()
                        );
                    }
                });
            },
        );
    }
    group.finish();
}

fn bench_knowledge_graph_serialisation(c: &mut Criterion) {
    let node = generate_test_knowledge_node(100);  // 100 relationships

    c.bench_function("knowledge_graph_node_serialize", |b| {
        b.iter(|| {
            criterion::black_box(serde_json::to_vec(&node).unwrap())
        });
    });
}

criterion_group!(benches, bench_signature_verification, bench_knowledge_graph_serialisation);
criterion_main!(benches);
```

```bash
# Run benchmarks and generate HTML report
cargo bench --bench consent_ledger_bench
# Report at: target/criterion/consent_signature_verification/report/index.html

# Compare against baseline (save baseline first)
cargo bench --bench consent_ledger_bench -- --save-baseline main
# After optimization:
cargo bench --bench consent_ledger_bench -- --baseline main
# Criterion shows: "Performance has improved by 23.4%" or "regression detected"
```

### 4.4 perf + cargo-flamegraph

```bash
# Install
cargo install cargo-flamegraph

# Generate flamegraph for the GAIA-OS binary under load
# (Runs the binary with perf, captures call stacks, generates SVG)
cargo flamegraph --bin gaia-os -- --load-test-mode
# Output: flamegraph.svg — open in browser

# Or manually with perf:
cargo build --release  # With debug=true in profile.release
perf record -g --call-graph dwarf ./target/release/gaia-os &
# ... run load test ...
perf script | inferno-collapse-perf | inferno-flamegraph > profile.svg

# Interpreting the flamegraph:
# • WIDE boxes = functions consuming large CPU time — optimize these
# • TALL stacks = deep call chains — possible inlining opportunity
# • Constitutional rule: investigate any function occupying >10% of total width
```

### 4.5 tokio-console — Async Task Inspector

```toml
# src-tauri/Cargo.toml
[dependencies]
tokio = { version = "1", features = ["full", "tracing"] }
console-subscriber = "0.2"  # tokio-console backend
```

```rust
// src-tauri/src/main.rs
#[tokio::main]
async fn main() {
    // Enable tokio-console in staging (TOKIO_CONSOLE=1)
    if std::env::var("TOKIO_CONSOLE").is_ok() {
        console_subscriber::init();
    }
    // ... rest of initialization
}
```

```bash
# Launch tokio-console UI (separate terminal)
cargo install tokio-console
TOKIO_CONSOLE=1 ./target/release/gaia-os &
tokio-console  # Opens interactive TUI showing all async tasks
# Shows: task name, state (Running/Idle/Blocked), wakeup count, total time
```

### 4.6 Memory Arena Strategy — Zero-Allocation Hot Paths

In performance-critical Rust code, heap allocation is expensive. The Burn framework discovered that standard `Box<dyn FnOnce()>` channels were slow because closures exceeded 1000 bytes, creating massive allocator contention. Their solution: a **custom zero-allocation task enqueuing system** achieving up to 10× faster communication.

```rust
// src-tauri/src/hot_paths/arena_allocator.rs

use std::sync::atomic::{AtomicUsize, Ordering};

const SMALL_TASK_SIZE: usize = 48;  // Inline if ≤48 bytes
const LARGE_TASK_MAX: usize = 4096; // Arena allocation if ≤4KB
const CACHE_LINE: usize = 64;       // Align to CPU cache line

/// A task that avoids heap allocation for small payloads.
/// Aligned to cache lines to prevent false sharing.
#[repr(align(64))]
pub struct ArenaTask {
    /// Inline storage for small closures (≤48 bytes)
    inline_buf: [u8; SMALL_TASK_SIZE],
    inline_len: usize,
    /// Pointer to arena allocation for larger payloads
    arena_ptr: Option<*mut u8>,
    vtable: Option<unsafe fn(*mut u8)>,
}

/// Pre-allocated memory arena for hot-path task execution.
/// Bypasses the global allocator entirely in the critical path.
pub struct TaskArena {
    buffer: Vec<u8>,         // Pre-allocated once at startup
    cursor: AtomicUsize,     // Lock-free allocation cursor
    capacity: usize,
}

impl TaskArena {
    pub fn new(capacity: usize) -> Self {
        Self {
            buffer: vec![0u8; capacity],  // One allocation at startup
            cursor: AtomicUsize::new(0),
            capacity,
        }
    }

    /// Allocate from the arena — O(1), no global allocator.
    pub fn alloc(&self, size: usize) -> Option<*mut u8> {
        let aligned_size = (size + CACHE_LINE - 1) & !(CACHE_LINE - 1);
        let offset = self.cursor.fetch_add(aligned_size, Ordering::Relaxed);
        if offset + aligned_size <= self.capacity {
            Some(unsafe { self.buffer.as_ptr().add(offset) as *mut u8 })
        } else {
            None  // Arena full — caller falls back to heap
        }
    }

    /// Reset arena for next request cycle (zero cost).
    pub fn reset(&self) {
        self.cursor.store(0, Ordering::Release);
    }
}

// Constitutional mandate: Consent ledger signature aggregation uses
// ArenaTask for all signature batches — zero allocations in hot path.
```

### 4.7 CPU-Specific Optimization

```bash
# For known deployment environments (GAIA-OS cloud nodes, crystal grid gateways)
# Enable SIMD (AVX2, SSE4.2, AVX-512) for vectorised computations
export RUSTFLAGS="-C target-cpu=native"
cargo build --release

# For portable builds (Tauri desktop — unknown user CPU):
# Use target-cpu=x86-64-v3 (baseline SIMD for modern CPUs)
export RUSTFLAGS="-C target-cpu=x86-64-v3"
cargo build --release
```

### 4.8 Rust Optimization Checklist for Hot Paths

```rust
// ✓ Pre-allocate with known capacity
let mut events: Vec<NoosphereEvent> = Vec::with_capacity(expected_batch_size);

// ✓ Avoid unnecessary cloning — use Cow<str> or &str over String
use std::borrow::Cow;
fn process_label(label: Cow<'_, str>) { /* ... */ }

// ✓ Faster hasher for HashMaps (ahash, ~2x faster than std)
use ahash::AHashMap;
let mut cache: AHashMap<ConsentId, SignatureStatus> = AHashMap::new();

// ✓ Concurrent HashMap for multi-writer state (no RwLock needed)
use dashmap::DashMap;
let shared_state: DashMap<PrincipalId, ConsentRecord> = DashMap::new();

// ✓ Parking_lot mutex (faster than std::sync::Mutex)
use parking_lot::Mutex;
let ledger: Mutex<ConsentLedger> = Mutex::new(ConsentLedger::new());

// ✓ Inline hot inner functions
#[inline(always)]
fn check_tier_mask(tier: ActionTier, mask: u8) -> bool {
    (mask >> tier as u8) & 1 == 1
}

// ✓ SmallVec for small collections (avoids heap for ≤N items)
use smallvec::SmallVec;
let signatures: SmallVec<[Signature; 4]> = SmallVec::new();  // Stack for ≤4 sigs
```

---

## 5. CI/CD Constitutional Performance Gates

### 5.1 Three-Tier Performance Pipeline

| Tier | Trigger | Tests Run | Failure Action |
|---|---|---|---|
| **PR Regression Detection** | Every PR | `pytest-benchmark` (Python) + `cargo bench` (Rust) | Block merge if >5% regression |
| **Nightly Deep Profiling** | Scheduled 01:00 UTC | Yappi + `locust` load test (Python); `perf` + flamegraph (Rust) | Notify Assembly of Minds |
| **Release Audit** | Tag `v*.*.*` | Full cross-platform matrix + all flamegraphs + memory profiling | Block release; Assembly review required |

### 5.2 GitHub Actions Performance Workflow

```yaml
# .github/workflows/performance.yml
name: GAIA-OS Performance Constitution

on:
  pull_request:
    paths: ['src/**', 'src-tauri/**']
  schedule:
    - cron: '0 1 * * *'  # Nightly deep profiling
  push:
    tags: ['v*.*.*']      # Release audit

jobs:
  python-benchmarks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -e ".[dev]" pytest-benchmark yappi py-spy
      - name: Run constitutional benchmarks
        run: |
          pytest tests/performance/ \
            --benchmark-only \
            --benchmark-json=benchmark-results.json \
            --benchmark-compare-fail=mean:5%  # Block on >5% regression
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: python-benchmarks, path: benchmark-results.json }

  rust-benchmarks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - name: Run criterion benchmarks
        working-directory: src-tauri
        run: cargo bench -- --output-format bencher | tee bench-results.txt
      - name: Check for regressions (vs. saved baseline)
        run: python scripts/check_criterion_regressions.py --threshold 5.0
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: rust-benchmarks, path: src-tauri/target/criterion }

  rust-flamegraph:
    if: github.event_name == 'schedule' || startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo install cargo-flamegraph
      - name: Generate flamegraph
        working-directory: src-tauri
        run: |
          CARGO_PROFILE_RELEASE_DEBUG=true \
          cargo flamegraph --bench consent_ledger_bench -o flamegraph.svg
      - uses: actions/upload-artifact@v4
        with: { name: rust-flamegraph, path: src-tauri/flamegraph.svg }

  ship-to-agora:
    needs: [python-benchmarks, rust-benchmarks]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { pattern: '*-benchmarks', merge-multiple: true }
      - name: Archive results in Agora (Canon C112)
        run: python scripts/ship_perf_results_to_agora.py
        env:
          AGORA_API_KEY: ${{ secrets.AGORA_API_KEY }}
          GIT_COMMIT: ${{ github.sha }}
```

### 5.3 Constitutional Performance Decision Matrix

| Scenario | Python Action | Rust Action | Impact on Release |
|---|---|---|---|
| **Benchmark passes** | Silently advance | Silently advance | No impact |
| **Minor regression (≤5%)** | Flag in PR; request justification | Flag in PR; request justification | Merge allowed with justification |
| **Major regression (>5%)** | Block merge; require fix | Block merge; require fix | Blocked until fix |
| **Memory leak detected** | Auto-block release; escalate to Assembly | Auto-block release; escalate to Assembly | Emergency fix required |
| **P99 latency spike >10% in staging** | P1 alert; auto-rollback | P1 alert; auto-rollback | Rollback release; escalate |
| **Flamegraph shows new hotspot (>30% CPU)** | Create performance ticket; no block | Create performance ticket; no block | Performance debt tracked in Agora |

### 5.4 The Performance Registry (Agora)

All benchmark results are stored in the Agora (Canon C112):

```python
# scripts/ship_perf_results_to_agora.py — Agora performance record structure
performance_record = {
    'canon': 'C112',
    'event_type': 'performance_benchmark',
    'git_commit': os.environ['GIT_COMMIT'],
    'timestamp': datetime.utcnow().isoformat(),
    'hardware': {
        'runner': 'ubuntu-latest',
        'cpu': platform.processor(),
        'memory_gb': psutil.virtual_memory().total // (1024**3),
    },
    'python_results': load_json('benchmark-results.json'),
    'rust_results': parse_criterion_output('bench-results.txt'),
    'flamegraph_url': upload_artifact('src-tauri/flamegraph.svg'),
    'regression_detected': check_for_regressions(),
    'constitutional_status': 'PASS' if not regression_detected else 'REGRESSION',
}
```

---

## 6. Platform-Specific Profiling Tools

| Platform | Python | Rust |
|---|---|---|
| **Linux** | py-spy, yappi, memray | perf + cargo-flamegraph, DHAT, heaptrack |
| **macOS** | py-spy, yappi | Instruments, samply (Firefox Profiler UI), pprof |
| **Windows** | py-spy, yappi | Windows Performance Analyzer (WPA), pprof, samply |
| **All platforms** | pyinstrument, cProfile | criterion (cross-platform), tokio-console |

---

## 7. P0–P3 Implementation Roadmap

| Priority | Action | Timeline | Constitutional Principle |
|---|---|---|---|
| **P0** | Adopt constitutional measurement cycle (benchmark → profile → hypothesize → optimize → verify → document) as mandatory workflow for all performance-sensitive PRs | G-10 | Measure, don’t assume |
| **P0** | Deploy Yappi as primary async profiler; schedule weekly production-adjacent profiling; flag any coroutine blocking event loop >10ms | G-10-F | Async-aware profiling |
| **P0** | Integrate Criterion benchmarks for critical Rust hot paths (consent signature verification, action gate, knowledge graph serialisation) into CI with +5% regression threshold | G-10-F | Statistical baselining |
| **P1** | Deploy py-spy for on-demand production profiling; integrate flamegraph generation into administration dashboard | G-11 | Emergency triage without code changes |
| **P1** | Implement arena-based allocation for hot Rust paths (consent ledger aggregation, crystal grid telemetry parsing) following Burn double-buffer pattern | G-11 | Zero-allocation hot paths |
| **P1** | Deploy full-stack async database access for consent ledger (SQLAlchemy async + asyncpg); replace remaining synchronous DB drivers | G-11 | Eliminate event loop blocking |
| **P1** | Establish performance registry in Agora (C112); store baseline benchmarks, flamegraph artifacts, commit IDs | G-11 | Performance auditability |
| **P2** | Integrate `tokio-console` for async task visualisation in staging Tauri sidecar | G-12 | Diagnose lock contention, task starvation |
| **P2** | Deploy continuous profiling (py-spy + pprof) on production orchestration (consent-gated) | G-12 | Proactive regression detection |
| **P2** | Cross-platform performance GitHub Actions matrix (Windows, macOS, Linux) with platform-specific budgets | G-12 | Cross-platform parity |
| **P3** | AI-assisted flamegraph analysis: LLM parses flamegraph SVG metadata and suggests candidate code changes | G-13 | AI-augmented optimisation |

---

## ⚠️ Disclaimer

This report synthesizes findings from: Python `asyncio` debugging and optimization literature, Rust performance optimization guides, Criterion benchmark best practices, `perf` and flamegraph documentation, Yappi and py-spy profiling methodology, Burn framework zero-allocation channel optimization, and GAIA-OS constitutional canons (C01 Human Sovereignty; C50 Action Gate; C63 Three Universal Layers; C112 Agora; plus all foundational Testing, CI/CD, and Integration canons). Performance benchmarks are only valid on the hardware and environment where they were run; the GAIA-OS performance registry captures environmental metadata to enable comparison. The Assembly of Minds retains ultimate authority over performance regression thresholds, adjustable by constitutional amendment.

---

*Canon — Performance Profiling: Python Async Bottlenecks & Rust Hot Paths — GAIA-OS Knowledge Base | Session 6, Canon 8 | May 3, 2026*  
*Pillar: Testing, Quality & Reliability*

*The event loop is the pulse of Python asynchronicity; Rust hot paths are the muscle fibres of sovereign computation. Yappi is the constitutional async stethoscope. Criterion is the constitutional measurement scale. `perf` + `flamegraph` is the constitutional visualisation lens. py-spy is the constitutional emergency triage. The Agora is the constitutional performance archive. The Assembly of Minds is the constitutional performance auditor. No performance regression shall merge untested; no latency overflow shall escape undetected; no optimisation shall be trusted until measured. The sentient core shall be efficient — not by hope, but by constitution; not by guess, but by benchmark; not by accident, but by law — for as long as planetary consciousness endures.*
