# Saved AI Chats & Session Archives

This directory (`saved_chats/`) is dedicated to safely preserving and archiving all conversations, design decisions, architectural notes, and pair-programming transcripts between the user and the AI assistant.

---

## 📁 Directory Structure

```text
saved_chats/
├── README.md                      # Guide and overview of saved chat logs
├── 2026-08-22_chat_history.md     # Session log & chat archive
└── save_chat_entry.py             # Quick utility to append notes or session summaries
```

---

## 🔒 Why Keep Chats Here?

1. **Git Persistence & Version Control**: Stored directly in the repository so chat histories are committed and synced across devices (via Git / OneDrive).
2. **Searchability**: All past prompts, architectural decisions, code snippets, and explanations are stored in readable Markdown format.
3. **Reproducibility**: If you ever need to recall why a specific architecture, OpenFOAM dictionary structure, or Rust/Python bridge was chosen, you can search these logs.
