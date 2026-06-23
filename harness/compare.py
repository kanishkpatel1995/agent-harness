#!/usr/bin/env python3
"""Side-by-side: run one question through every compaction policy, offline.

    python -m harness.compare "quantum networking startups"
    python -m harness.compare "..." --verbose      # show what each window kept

The point of the demo: watch the policies FORGET DIFFERENTLY in real time. We
plant a checkable fact (a codename) in the sources, force the window over budget,
and for each policy show: how many LLM calls it cost, how big the resulting window
is, whether it retrieves at answer time, and — the punchline — whether the planted
fact survives. Truncate drops it, summaries blur it, externalize retrieves it, and
the hybrid is the cheap-ish one that still recovers it.

Runs fully offline with a deterministic fake summarizer (no API key, no network),
so it's safe on stage. Swap in a real LLM + Chroma store for the live thing.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.policies import POLICIES, Store  # noqa: E402

NEEDLE = "BLUEFIN-2027"
QUESTION = "What is the internal codename and the ship date?"


class _Resp:
    def __init__(self, content, usage):
        self.content = content
        self.usage = usage


class FakeSummarizer:
    """Deterministic, offline. Summarizes by KEEPING the topic and DROPPING the
    specifics — exactly the lossy behavior that makes summary-only policies fail.
    """

    def complete(self, messages):
        transcript = messages[-1]["content"]
        in_tok = max(1, len(transcript) // 4)
        summary = ("[summary] Background, method, and trade-offs discussed; "
                   "exact identifiers and dates were compressed out.")
        return _Resp(summary, {"prompt_tokens": in_tok, "completion_tokens": len(summary) // 4})


def _sources(topic: str) -> list[dict]:
    """Six 'old' turns the window must shed; one carries the planted fact."""
    base = [
        f"Overview of {topic}: the landscape, the main players, and why it matters.",
        f"Methodology notes on {topic}: how teams typically approach the problem.",
        # the needle — high-signal: digits + a codename, so 'importance' keeps it
        f"Project record: internal codename {NEEDLE}; the confirmed ship date is 2027-03-14. "
        f"Budget line 4471 approved.",
        f"Market commentary on {topic}: adoption is uneven and contested.",
        f"Risks and open questions around {topic} that remain unresolved.",
        f"Related work and prior art relevant to {topic}.",
    ]
    return [{"role": "tool", "content": b} for b in base]


def _approx(msgs) -> int:
    return sum(len(m.get("content") or "") for m in msgs) // 4


def run(topic: str, verbose: bool = False):
    old = _sources(topic)
    llm = FakeSummarizer()
    goal = {"role": "system", "content": f"GOAL: research '{topic}' and answer: {QUESTION}"}
    recent = {"role": "user", "content": f"Now answer: {QUESTION}"}

    print(f"\n  topic    : {topic}")
    print(f"  question : {QUESTION}")
    print(f"  planted  : codename {NEEDLE}, ship date 2027-03-14  (in 1 of {len(old)} sources)\n")
    print(f"  {'policy':<19}{'architecture':<13}{'llm':>4}{'ctx tok':>9}{'retr':>6}{'  fact?':<8}")
    print("  " + "-" * 60)

    rows = []
    for name, pol in POLICIES.items():
        store = Store()
        block, usage = pol.compact(old, llm, store)
        window = [goal] + block + [recent]
        retrieved = store.search(QUESTION, k=2) if pol.retrieves else []
        seen = " ".join(m.get("content") or "" for m in window) + " " + " ".join(retrieved)
        survived = NEEDLE in seen
        llm_calls = _calls(name, old)
        ctx = _approx(window)
        mark = "PASS" if survived else "lost"
        rows.append((name, pol, llm_calls, ctx, pol.retrieves, survived))
        print(f"  {C.B}{name:<19}{C.E}{pol.architecture:<13}{llm_calls:>4}{ctx:>9}"
              f"{('yes' if pol.retrieves else '-'):>6}"
              f"   {(C.G+'✓ kept'+C.E) if survived else (C.D+'✗ '+mark+C.E)}")
        if verbose:
            kept = " | ".join((m.get('content') or '').replace(chr(10), ' ')[:50] for m in block)
            print(f"  {C.D}      kept: {kept}{C.E}")
            if retrieved:
                print(f"  {C.D}      retrieved: {retrieved[0][:60]}…{C.E}")

    print("  " + "-" * 60)
    keep = [r[0] for r in rows if r[5]]
    print(f"\n  fact survived in: {C.G}{', '.join(keep)}{C.E}")
    print(f"  {C.D}truncate drops it · summaries blur it · externalize & hybrid recover it"
          f" — and hybrid is the cheap one that still does.{C.E}\n")


def _calls(name: str, old) -> int:
    return {"recency": 1, "importance": 1, "semantic": 2,
            "subagent": sum(1 for m in old if (m.get("content") or "").strip()),
            "reversible_hybrid": 1}.get(name, 0)


class C:
    B = "\033[1m"; G = "\033[38;5;71m"; D = "\033[2m"; E = "\033[0m"


def main():
    ap = argparse.ArgumentParser(description="Compare compaction policies side by side (offline).")
    ap.add_argument("topic", nargs="*", help="a research topic (flavor for the sources)")
    ap.add_argument("--verbose", action="store_true", help="show what each policy kept / retrieved")
    args = ap.parse_args()
    run(" ".join(args.topic) or "quantum networking startups", verbose=args.verbose)


if __name__ == "__main__":
    main()
