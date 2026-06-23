#!/usr/bin/env python3
"""EXP-007 — does LangChain's shipped summary-buffer beat our 15-line `recency`?

Both are COMPACT arms (a rolling summary, no retrieval). Same FRAMES questions, the
same 8B summarizer model (LangChain reaches it via ChatOpenAI -> NIM, no OpenAI spend),
and the same 70B judge. One run dir, two policies; report() prints the head-to-head.

The point of the arm: measure the framework default instead of assuming it. If a
15-line hand-rolled policy matches a popular framework's memory, that is worth knowing.

    python experiments/applied/launch_exp007_langchain.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.applied.runner import Config, run, report  # noqa: E402
from experiments.bench.logsetup import setup  # noqa: E402

CFG = Config(
    exp_id="EXP-007",
    slug="frames-langchain-vs-recency",
    hypothesis=(
        "LangChain's ConversationSummaryBufferMemory (the framework's shipped default) does "
        "not beat our 15-line `recency` on FRAMES: both are rolling-summary compaction, so "
        "they land in the same accuracy band; the framework adds a dependency, not accuracy."
    ),
    assumptions=(
        "Both arms summarize on the same 8B model (LangChain via an OpenAI-compatible NIM endpoint).",
        "Oracle articles + budget 1500 + chunked reads force many compaction events per question.",
        "The 70b judge grades both arms identically.",
        "LangChain summarization tokens are captured via get_openai_callback for a fair cost axis.",
    ),
    model="meta/llama-3.1-8b-instruct",
    use_judge=True,
    policies=("recency", "langchain_summary"),
    n_questions=20,
    max_articles=6,
    budget=1500,
    chunk_chars=1500,
    keep_recent=4,
    seed=7,
)


if __name__ == "__main__":
    setup("INFO")
    report(run(CFG))
