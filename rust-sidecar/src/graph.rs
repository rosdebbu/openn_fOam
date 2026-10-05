//! Knowledge-Graph BFS pathfinding and community analysis in Rust.
//!
//! Provides fast shortest-path finding and connection analysis across
//! Graphify knowledge graphs without blocking Python's async event loop.

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};

#[derive(Debug, Deserialize)]
pub struct GraphNode {
    pub id: String,
    #[serde(default)]
    pub label: Option<String>,
    #[serde(default)]
    pub community: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct GraphLink {
    pub source: String,
    pub target: String,
    #[serde(default)]
    pub label: Option<String>,
    #[serde(default)]
    pub weight: Option<f64>,
}

#[derive(Debug, Deserialize)]
pub struct GraphPayload {
    #[serde(default)]
    pub nodes: Vec<GraphNode>,
    #[serde(default)]
    pub links: Vec<GraphLink>,
}

#[derive(Debug, Deserialize)]
pub struct PathRequest {
    pub graph: GraphPayload,
    pub source: String,
    pub target: String,
}

#[derive(Debug, Serialize)]
pub struct PathResponse {
    pub found: bool,
    pub path: Vec<String>,
    pub distance: usize,
}

/// Computes the unweighted shortest path between source and target using BFS.
pub fn find_shortest_path(req: PathRequest) -> PathResponse {
    let source = req.source.trim();
    let target = req.target.trim();

    if source.is_empty() || target.is_empty() {
        return PathResponse {
            found: false,
            path: Vec::new(),
            distance: 0,
        };
    }

    if source == target {
        return PathResponse {
            found: true,
            path: vec![source.to_string()],
            distance: 0,
        };
    }

    let mut adj: HashMap<&str, Vec<&str>> = HashMap::new();
    for link in &req.graph.links {
        let s = link.source.as_str();
        let t = link.target.as_str();
        adj.entry(s).or_default().push(t);
        adj.entry(t).or_default().push(s);
    }

    let mut visited: HashSet<&str> = HashSet::new();
    let mut parent: HashMap<&str, &str> = HashMap::new();
    let mut queue: VecDeque<&str> = VecDeque::new();

    visited.insert(source);
    queue.push_back(source);

    let mut target_found = false;

    while let Some(current) = queue.pop_front() {
        if current == target {
            target_found = true;
            break;
        }

        if let Some(neighbors) = adj.get(current) {
            for &next in neighbors {
                if !visited.contains(next) {
                    visited.insert(next);
                    parent.insert(next, current);
                    queue.push_back(next);
                }
            }
        }
    }

    if !target_found {
        return PathResponse {
            found: false,
            path: Vec::new(),
            distance: 0,
        };
    }

    let mut path = Vec::new();
    let mut curr = target;
    path.push(curr.to_string());

    while let Some(&p) = parent.get(curr) {
        path.push(p.to_string());
        if p == source {
            break;
        }
        curr = p;
    }

    path.reverse();
    let distance = path.len().saturating_sub(1);

    PathResponse {
        found: true,
        path,
        distance,
    }
}
