//! Codebase token estimation and symbol scanner in Rust.
//!
//! Provides lightning-fast token, line, character, and symbol metrics
//! to help OpenZess prune prompts and enforce context limits.

use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct CodeStatsRequest {
    pub text: String,
}

#[derive(Debug, Serialize)]
pub struct CodeStatsResponse {
    pub char_count: usize,
    pub word_count: usize,
    pub line_count: usize,
    pub non_empty_lines: usize,
    pub estimated_tokens: usize,
    pub is_balanced: bool,
}

pub fn analyze_code(req: CodeStatsRequest) -> CodeStatsResponse {
    let text = &req.text;
    let char_count = text.chars().count();
    let word_count = text.split_whitespace().count();
    let line_count = text.lines().count();
    let non_empty_lines = text.lines().filter(|l| !l.trim().is_empty()).count();

    // Fast heuristic token estimation:
    let approx_by_chars = (char_count as f64 / 3.8).ceil() as usize;
    let estimated_tokens = word_count.max(approx_by_chars);

    // Balanced delimiter check for code sanity
    let mut stack = Vec::new();
    let mut is_balanced = true;

    for ch in text.chars() {
        match ch {
            '(' | '[' | '{' => stack.push(ch),
            ')' => {
                if stack.pop() != Some('(') {
                    is_balanced = false;
                    break;
                }
            }
            ']' => {
                if stack.pop() != Some('[') {
                    is_balanced = false;
                    break;
                }
            }
            '}' => {
                if stack.pop() != Some('{') {
                    is_balanced = false;
                    break;
                }
            }
            _ => {}
        }
    }

    if !stack.is_empty() {
        is_balanced = false;
    }

    CodeStatsResponse {
        char_count,
        word_count,
        line_count,
        non_empty_lines,
        estimated_tokens,
        is_balanced,
    }
}
