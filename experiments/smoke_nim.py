"""Smoke test — run this BEFORE the bake-off.

Confirms (a) the key loads, (b) the catalog is reachable and our two chosen model
IDs actually exist, (c) a tiny completion round-trips. ~2 API calls total.

    python experiments/smoke_nim.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.nim import NimLLM

DEV = "meta/llama-3.1-8b-instruct"
FINAL = "meta/llama-3.3-70b-instruct"


def main():
    try:
        llm = NimLLM(model=DEV)
    except Exception as e:
        print(f"[smoke] FAILED to init: {type(e).__name__}: {e}")
        return 1
    print(f"[smoke] key loaded OK; dev model = {DEV}")

    # 1) catalog
    catalog = []
    try:
        catalog = llm.list_models()
        print(f"[smoke] GET /v1/models -> {len(catalog)} models in catalog")
        for want in (DEV, FINAL):
            print(f"   {'FOUND  ' if want in catalog else 'MISSING'} {want}")
        rel = [m for m in catalog if any(
            k in m for k in ("llama-3.3", "llama-3.1", "llama3", "nemotron", "qwen", "mistral", "deepseek")
        )]
        print(f"[smoke] {len(rel)} relevant chat IDs; first 30:")
        for m in rel[:30]:
            print("   ", m)
    except Exception as e:
        print(f"[smoke] list_models FAILED: {type(e).__name__}: {e}")

    # 2) one tiny completion (only if dev model is present, else skip the spend)
    if DEV in catalog or not catalog:
        try:
            r = llm.complete([{"role": "user", "content": "Reply with exactly one word: PONG"}])
            print(f"[smoke] completion OK (cached={r.cached}); content={r.content!r}; usage={r.usage}")
        except Exception as e:
            print(f"[smoke] completion FAILED: {type(e).__name__}: {e}")
    else:
        print(f"[smoke] skipping completion — {DEV} not in catalog; pick a listed ID above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
