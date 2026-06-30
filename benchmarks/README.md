# GAIA Benchmarks

Benchmark results are the **ground truth** for performance claims.
No performance claim in documentation or ADRs is valid without a corresponding benchmark.

## Benchmark Categories

| Category | What It Measures | Target (v0.1) |
|---|---|---|
| `pipeline_latency` | End-to-end minimal pipeline time | < 2 seconds |
| `sync_throughput` | Claims synced per second across nodes | > 100/s |
| `consensus_latency` | Time for 3-node consensus to converge | < 500ms |
| `snapshot_load` | Time to reload a 10k-claim snapshot | < 1 second |
| `simulation_run` | Time for a 10-step simulation | < 5 seconds |

## Running Benchmarks

```bash
python benchmarks/pipeline_latency.py
python benchmarks/sync_throughput.py
```

## Benchmark Files

- `pipeline_latency.py` — measures the v0.1 minimal pipeline end-to-end
- `sync_throughput.py` — measures cross-node state synchronisation throughput
- `consensus_latency.py` — measures time to consensus across N nodes

## Recording Results

After running benchmarks, record results in `benchmarks/results/YYYY-MM-DD.json`.
Results must include: machine spec, GAIA version, run timestamp, metric values.
