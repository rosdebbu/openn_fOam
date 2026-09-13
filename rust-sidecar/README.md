# 🦀 OpenZess Rust Sidecar & Bare-Metal CFD Engine

High-performance native computational kernel for OpenZess Studio, providing:
- **Bare-Metal Navier-Stokes Simulation:** Parallel pressure Poisson solver and momentum updates.
- **Microsecond Benchmarks:** Computational throughput testing (Million cells/sec, steps/sec).
- **Graphify BFS:** High-speed knowledge graph traversal and shortest-path search.
- **Cosine Vector Top-K:** Zero-overhead context search for physics datasets.
- **Fast Image Codec:** Raw screen-buffer encoding.

## Running Locally

```bash
cargo run --release
```

The sidecar will start on `http://127.0.0.1:8081`.

## Endpoints

- `GET /health` — Service status and capabilities
- `POST /cfd/solve` — Advance 2D Navier-Stokes cavity/channel flow by $N$ steps
- `POST /cfd/benchmark` — Measure raw throughput and CFL stability numbers
- `POST /graph/shortest-path` — BFS pathfinding through Graphify knowledge graphs
- `POST /vector/top-k` — Cosine similarity ranking
- `POST /code/stats` — Codebase metrics and token estimation
