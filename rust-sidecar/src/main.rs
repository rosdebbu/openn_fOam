//! OpenZess Rust Sidecar & CFD Engine.
//!
//! A high-performance Axum microservice exposing stateless, bare-metal CPU-bound
//! helpers and parallel Navier-Stokes solvers for OpenZess Studio.

mod cfd_solver;
mod code_stats;
mod graph;
mod imaging;
mod vector;

use axum::{
    extract::{DefaultBodyLimit, HeaderMap},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde_json::json;
use std::net::SocketAddr;
use tower_http::cors::{Any, CorsLayer};

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/health", get(health_check))
        // CFD Simulation & Benchmarking Endpoints
        .route("/cfd/solve", post(cfd_solve_handler))
        .route("/cfd/benchmark", post(cfd_benchmark_handler))
        // Knowledge Graph & Vector Endpoints
        .route("/graph/shortest-path", post(graph_shortest_path_handler))
        .route("/vector/top-k", post(vector_top_k_handler))
        .route("/code/stats", post(code_stats_handler))
        .route("/image/encode", post(image_encode_handler))
        .layer(DefaultBodyLimit::max(50 * 1024 * 1024))
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
                .allow_methods(Any)
                .allow_headers(Any),
        );

    let port: u16 = std::env::var("PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8081);

    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    println!("🦀 OpenZess Rust Sidecar & CFD Engine listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("Failed to bind Rust sidecar port");

    axum::serve(listener, app).await.expect("Sidecar server error");
}

async fn health_check() -> impl IntoResponse {
    Json(json!({
        "status": "ok",
        "service": "OpenZess Rust Sidecar & CFD Engine",
        "version": env!("CARGO_PKG_VERSION"),
        "capabilities": [
            "cfd_navier_stokes_2d",
            "cfd_benchmark",
            "graph_shortest_path_bfs",
            "vector_cosine_top_k",
            "code_token_estimator",
            "pixel_buffer_encoder"
        ]
    }))
}

async fn cfd_solve_handler(Json(payload): Json<cfd_solver::CfdConfig>) -> impl IntoResponse {
    let result = cfd_solver::run_simulation(payload);
    Json(result)
}

async fn cfd_benchmark_handler(Json(payload): Json<cfd_solver::CfdConfig>) -> impl IntoResponse {
    let result = cfd_solver::run_benchmark(payload);
    Json(result)
}

async fn graph_shortest_path_handler(Json(payload): Json<graph::PathRequest>) -> impl IntoResponse {
    let result = graph::find_shortest_path(payload);
    Json(result)
}

async fn vector_top_k_handler(Json(payload): Json<vector::TopKRequest>) -> impl IntoResponse {
    let result = vector::compute_top_k(payload);
    Json(result)
}

async fn code_stats_handler(Json(payload): Json<code_stats::CodeStatsRequest>) -> impl IntoResponse {
    let result = code_stats::analyze_code(payload);
    Json(result)
}

async fn image_encode_handler(headers: HeaderMap, body: axum::body::Bytes) -> Response {
    let width: u32 = match headers.get("x-width").and_then(|v| v.to_str().ok()).and_then(|s| s.parse().ok()) {
        Some(w) => w,
        None => return (StatusCode::BAD_REQUEST, "missing or invalid x-width header").into_response(),
    };
    let height: u32 = match headers.get("x-height").and_then(|v| v.to_str().ok()).and_then(|s| s.parse().ok()) {
        Some(h) => h,
        None => return (StatusCode::BAD_REQUEST, "missing or invalid x-height header").into_response(),
    };
    let layout = headers.get("x-layout").and_then(|v| v.to_str().ok()).unwrap_or("bgrx");
    let format = headers.get("x-format").and_then(|v| v.to_str().ok()).unwrap_or("jpeg");
    let quality: u8 = headers.get("x-quality").and_then(|v| v.to_str().ok()).and_then(|s| s.parse().ok()).unwrap_or(85);

    match imaging::encode(&body, width, height, layout, format, quality) {
        Ok((bytes, mime)) => (
            StatusCode::OK,
            [("content-type", mime)],
            bytes,
        ).into_response(),
        Err(err) => (StatusCode::BAD_REQUEST, err).into_response(),
    }
}
