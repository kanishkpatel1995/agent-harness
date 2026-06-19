"""Central config — change a budget, a model, or an axis HERE, not in ten places.
That single-source-of-truth is what lets the experiment scale.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Config:
    # --- model / API ---
    model: str = "meta/llama-3.1-8b-instruct"
    # The HARD ceiling. llama-3.1/3.3 are 128k. Set LOW (e.g. 4000) to demonstrate
    # the context-overflow wall cheaply; set to the real 128000 for the true run.
    model_max_tokens: int = 4000
    temperature: float = 0.2
    min_interval: float = 1.6

    # --- experiment identity (protocol: every experiment states these) ---
    exp_id: str = "EXP-001"
    slug: str = "compaction-bakeoff"
    hypothesis: str = (
        "Under a fixed token budget, summary-based compaction (recency / importance "
        "/ semantic) preserves more needle-facts per token than truncation, and there "
        "is a budget B* that trades compaction fact-loss against lost-in-the-middle."
    )
    assumptions: tuple = (
        "Needle-fact recall is a valid proxy for task-relevant information retention.",
        "approx_tokens (~4 chars/token) is an acceptable estimate for budget gating.",
        "The summarizer model is held fixed across policies within a run.",
        "Coined needle tokens are not recoverable from model priors (only from context).",
        "Synthetic transcripts approximate the compaction dynamics of a real agent run.",
    )

    # --- experiment axes ---
    policies: tuple = ("truncate", "recency", "importance", "semantic")
    budgets: tuple = (1000, 2000)          # compaction budget B — the swept axis
    run_lengths: tuple = (4, 8)            # how many sources arrive
    seeds: tuple = (0, 1)
    keep_recent: int = 4

    # --- data ---
    dataset: str = "synthetic"             # "synthetic" | "hf:<name>" (later)
    n_needles: int = 8

    # --- baseline ---
    include_baseline: bool = True          # the no-compaction recall-vs-length arm

    # --- io ---
    results_path: str = "experiments/bench/results.csv"
    cache_dir: str = "experiments/.cache"
    log_level: str = "INFO"

    def cells(self):
        """Every (policy, budget, run_length, seed) cell in the compaction sweep."""
        return [
            (p, b, L, s)
            for p in self.policies
            for b in self.budgets
            for L in self.run_lengths
            for s in self.seeds
        ]


# A small, fast preset for plumbing/dev on the cheap 8b model.
DEV = Config()

# The real run: stronger model, more budgets + lengths + seeds, real 128k ceiling.
FULL = Config(
    model="meta/llama-3.3-70b-instruct",
    model_max_tokens=128_000,
    budgets=(1000, 2000, 4000, 8000),
    run_lengths=(4, 8, 16, 32),
    seeds=(0, 1, 2, 3, 4),
)
