"""Read results.csv -> the three things the paper needs:
  1. compaction: probe recall (mean ± real sd) and cost, by policy x budget.
  2. baseline:   recall vs run-length, and where the context-overflow wall hits.
  3. a B* hint:  the budget with the best probe recall per policy.
"""

from __future__ import annotations

import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

from .logsetup import get

log = get("analyze")


def report(cfg, results_path=None):
    from .run_context import latest_results

    p = Path(results_path) if results_path else (latest_results() or Path(cfg.results_path))
    if not p.exists():
        log.warning("no results yet — run the sweep first")
        return
    log.info(f"analyzing {p}")
    rows = list(csv.DictReader(p.open()))
    comp = [r for r in rows if r["arm"] == "compaction"]
    base = [r for r in rows if r["arm"] == "baseline"]

    if comp:
        # Recall as a FRACTION (probe / needles_total) so cells with different
        # needle counts (L=4 -> 4 needles, L=8 -> 8) pool correctly. This fixes
        # the earlier bug that averaged raw counts across mismatched totals.
        g = defaultdict(lambda: defaultdict(list))
        for r in comp:
            k = (r["policy"], int(r["budget"]))
            need = max(1, int(r["needles_total"]))
            g[k]["probe"].append(int(r["probe"]) / need)
            g[k]["fid"].append(int(r["fidelity"]) / need)
            g[k]["tok"].append(int(r["tokens_total"]))
        print("\n=== compaction: probe recall RATE (mean±sd) and cost, by policy × budget ===")
        print(f"{'policy':<12}{'budget':>7}{'probe_rate':>16}{'fidelity':>10}{'tokens':>9}")
        best = {}
        for (pol, b) in sorted(g):
            a = g[(pol, b)]
            n = len(a["probe"])
            pm = st.mean(a["probe"]); psd = st.pstdev(a["probe"]) if n > 1 else 0.0
            fm = st.mean(a["fid"]); tm = st.mean(a["tok"])
            print(f"{pol:<12}{b:>7}{pm:>9.2f}±{psd:<5.2f}{fm:>10.2f}{tm:>9.0f}")
            if pol not in best or pm > best[pol][1]:
                best[pol] = (b, pm)
        print("\nB* hint (budget with best probe recall rate, per policy):")
        for pol, (b, pm) in sorted(best.items()):
            print(f"  {pol:<12} B*={b}  (probe rate {pm:.2f})")

    if base:
        bg = defaultdict(list)
        ov = defaultdict(list)
        for r in base:
            need = max(1, int(r["needles_total"]))
            bg[int(r["run_length"])].append(int(r["probe"]) / need)
            ov[int(r["run_length"])].append(int(r["overflow"]))
        print("\n=== baseline (no compaction): recall RATE vs length, overflow wall ===")
        print(f"{'run_length':>10}{'probe_rate':>13}{'overflowed?':>13}")
        for L in sorted(bg):
            hit = any(x for x in ov[L])
            print(f"{L:>10}{st.mean(bg[L]):>13.2f}{('yes' if hit else 'no'):>13}")

    log.info("analysis done")
