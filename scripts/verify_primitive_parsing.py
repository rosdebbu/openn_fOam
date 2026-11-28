"""Reproduce the "model parts were almost never used" finding.

Run from the repo root:  python scripts/verify_primitive_parsing.py
Needs: torch, transformers, peft, the cached Qwen/Qwen3-0.6B base, and openzess_qwen3_0.6b_rl/.

One generation per prompt (300 new tokens, seed 0, temperature 0.4 as in backend/app.py).
The OLD method sees only the first 180 tokens and needs the whole reply to be valid JSON.
The NEW method is backend.app._parse_primitives on all 300 tokens.
"""
import json
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

import backend.app as A  # the project's own prompt, sanitizer and new parser

BASE = "Qwen/Qwen3-0.6B"
OLD_LIMIT = 180
PROMPTS = [
    "a simple flying saucer", "a stone bridge with two pillars", "a dragon", "a rocket with fins",
    "a heart valve", "a shipping container in wind", "a windmill", "a wall with a gap",
    "a golf ball", "a skyscraper next to a small house", "an octopus", "a pyramid in a sandstorm",
]


def old_parse(raw: str) -> list:
    """The logic before the fix: json.loads on the whole reply."""
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return []
    try:
        return A._sanitize_primitives(json.loads(m.group(0)).get("primitives"))
    except Exception:
        return []


device = "cuda" if torch.cuda.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(BASE, local_files_only=True)
base = AutoModelForCausalLM.from_pretrained(
    BASE, dtype=torch.bfloat16 if device == "cuda" else torch.float32, device_map=device, local_files_only=True
)
model = PeftModel.from_pretrained(base, str(ROOT / "openzess_qwen3_0.6b_rl")).eval()

old_ok = new_ok = 0
print(f"{'prompt':38} old(180 tok)  new(300 tok)")
for p in PROMPTS:
    msgs = [{"role": "system", "content": A._PRIMITIVE_SYSTEM_PROMPT}, {"role": "user", "content": p}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    ids = tok(text, return_tensors="pt").to(device)
    torch.manual_seed(0)
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=300, do_sample=True, temperature=0.4, top_p=0.9, pad_token_id=tok.eos_token_id)
    new_ids = out[0][ids["input_ids"].shape[-1]:]
    full = tok.decode(new_ids, skip_special_tokens=True)
    cut = tok.decode(new_ids[:OLD_LIMIT], skip_special_tokens=True)
    o, n = old_parse(cut), A._parse_primitives(full)[0]
    old_ok += bool(o)
    new_ok += bool(n)
    print(f"{p[:36]!r:38} {len(o)} parts       {len(n)} parts  [{','.join(x['kind'] for x in n)}]")
print(f"\nOLD method usable: {old_ok}/{len(PROMPTS)}   NEW method usable: {new_ok}/{len(PROMPTS)}")
