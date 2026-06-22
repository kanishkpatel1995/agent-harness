#!/usr/bin/env python3
"""CLI entrypoint.

Examples:
    # Offline, deterministic, no API key (the stage demo):
    python run.py "context engineering for long-running agents"

    # Real model via litellm (needs an API key in .env):
    python run.py --real --model gpt-4o-mini "your topic"

    # Local model (Ollama):
    python run.py --real --model ollama/llama3.1 "your topic"

`--real` swaps FakeLLM for a live model; `--model` overrides HARNESS_MODEL. The
offline path uses cached web fixtures; set HARNESS_OFFLINE=0 for real search/fetch.
"""

import argparse
import os
import sys

from harness import FakeLLM, LLMClient, build_agent


def main():
    ap = argparse.ArgumentParser(description="Run the deep-research agent harness.")
    ap.add_argument("goal", nargs="*", help="What to research")
    ap.add_argument("--real", action="store_true", help="Use a real model via litellm (else FakeLLM)")
    ap.add_argument("--model", default=None, help="Override HARNESS_MODEL")
    ap.add_argument("--context", type=int, default=3000, help="Max context tokens before compaction")
    ap.add_argument("--max-usd", type=float, default=1.00, help="Hard cost cap (real models)")
    ap.add_argument("--max-steps", type=int, default=30)
    args = ap.parse_args()

    goal = " ".join(args.goal) or "context engineering for long-running LLM agents"

    if args.real:
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass
        llm = LLMClient(model=args.model)
        print(f"[real model: {llm.model}]")
    else:
        llm = FakeLLM()
        os.environ.setdefault("HARNESS_OFFLINE", "1")
        print("[FakeLLM: offline, deterministic — no API key, no network]")

    run = build_agent(
        goal,
        llm,
        max_context_tokens=args.context,
        max_steps=args.max_steps,
        max_usd=args.max_usd,
    )
    answer = run()

    print("\n" + "=" * 64)
    print("FINAL REPORT")
    print("=" * 64)
    print(answer)
    print("\n" + "-" * 64)
    print(f"Scratchpad: {run.scratchpad.path}  ({run.scratchpad.count()} notes)")
    print(run.budget.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
