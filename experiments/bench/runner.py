"""Run the sweep: compaction cells (policy x budget x run_length x seed) plus the
no-compaction baseline (run_length x seed). Checkpointed + resumable per cell.
"""

from __future__ import annotations

import csv
from pathlib import Path

from experiments.nim import NimLLM
from . import datasets, window
from .policies import build as build_policies
from .logsetup import get

log = get("runner")

FIELDS = ["arm", "policy", "budget", "run_length", "seed", "needles_total",
          "fidelity", "probe", "n_compactions", "final_window_tokens", "overflow",
          "tokens_in", "tokens_out", "tokens_total"]


def _done(path):
    p = Path(path)
    if not p.exists():
        return set()
    with p.open() as f:
        return {(r["arm"], r["policy"], r["budget"], r["run_length"], r["seed"])
                for r in csv.DictReader(f)}


def _append(path, row):
    p = Path(path)
    new = not p.exists()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def run(cfg):
    from .run_context import RunContext

    ctx = RunContext(cfg)
    llm = NimLLM(model=cfg.model, temperature=cfg.temperature,
                 min_interval=cfg.min_interval, cache_dir=cfg.cache_dir,
                 transcript_path=ctx.transcript_path)
    pols = build_policies(cfg.policies)
    done = _done(ctx.results_path)

    log.info(f"model={cfg.model} max_window={cfg.model_max_tokens}")
    log.info(f"policies={list(pols)} budgets={list(cfg.budgets)} "
             f"run_lengths={list(cfg.run_lengths)} seeds={list(cfg.seeds)}")
    log.info(f"{len(cfg.cells())} compaction cells"
             f"{' + baseline' if cfg.include_baseline else ''}; {len(done)} already done")

    # --- compaction arm ---
    for (pname, budget, L, s) in cfg.cells():
        key = ("compaction", pname, str(budget), str(L), str(s))
        if key in done:
            log.debug(f"skip done {key}")
            continue
        pol = pols.get(pname)
        if pol is None:
            continue
        try:
            sample = datasets.load(cfg.dataset, L, cfg.n_needles, s)
            row = window.run_compaction(pol, sample, llm, budget=budget,
                                        keep_recent=cfg.keep_recent,
                                        model_max_tokens=cfg.model_max_tokens)
        except Exception as e:  # one bad cell must not kill the sweep
            log.error(f"cell {key} FAILED: {type(e).__name__}: {e}")
            continue
        row.update({"run_length": L, "seed": s})
        _append(ctx.results_path, row)
        log.info(f"CELL {pname} B={budget} L={L} s={s} -> "
                 f"fid={row['fidelity']} probe={row['probe']} tok={row['tokens_total']}")

    # --- baseline arm ---
    if cfg.include_baseline:
        for L in cfg.run_lengths:
            for s in cfg.seeds:
                key = ("baseline", "none", "0", str(L), str(s))
                if key in done:
                    continue
                try:
                    sample = datasets.load(cfg.dataset, L, cfg.n_needles, s)
                    row = window.run_baseline(sample, llm, model_max_tokens=cfg.model_max_tokens)
                except Exception as e:
                    log.error(f"baseline L={L} s={s} FAILED: {type(e).__name__}: {e}")
                    continue
                row.update({"run_length": L, "seed": s})
                _append(ctx.results_path, row)
                log.info(f"BASELINE L={L} s={s} -> probe={row['probe']} "
                         f"overflow={row['overflow']} raw_tok={row['final_window_tokens']}")

    log.info(f"sweep complete -> {ctx.results_path}")
    return ctx
