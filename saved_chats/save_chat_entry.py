"""
Utility script to quickly append or create a saved chat entry in the saved_chats/ folder.

Usage:
    python saved_chats/save_chat_entry.py "Session Topic" "Detailed notes or chat transcript"
"""

import sys
from datetime import datetime
from pathlib import Path

SAVED_CHATS_DIR = Path(__file__).resolve().parent

def save_entry(title: str, content: str):
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    filename = SAVED_CHATS_DIR / f"{today_str}_chat_history.md"
    
    is_new = not filename.exists()
    
    with open(filename, "a", encoding="utf-8") as f:
        if is_new:
            f.write(f"# AI Chat Archive — {today_str}\n\n")
            f.write("This file contains recorded chats, decisions, and transcripts.\n\n---\n\n")
        
        f.write(f"## 📝 Entry: {title}\n")
        f.write(f"**Recorded at**: `{timestamp_str}`\n\n")
        f.write(f"{content}\n\n")
        f.write("---\n\n")
    
    try:
        print(f"[SAVED] Successfully saved chat entry to: {filename}")
    except Exception:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python saved_chats/save_chat_entry.py \"<Title>\" \"<Content>\"")
    else:
        title_arg = sys.argv[1]
        content_arg = sys.argv[2]
        save_entry(title_arg, content_arg)
