"""Bootstrap CIs and paired significance for the compaction bake-off.

For a results.csv this reports, per arm, the accuracy with a 95% bootstrap confidence
interval, and for any arm pairs the accuracy difference, its paired-bootstrap 95% CI, and
McNemar's exact two-sided p-value. Pairing is on the question key (qid, plus conv for LoCoMo),
because every arm answers the same questions. Pure Python, no scipy, seeded.

    python experiments/stats.py <results.csv> [armA:armB ...]
"""

from __future__ import annotations

import csv
import math
import random
import sys
from collections import defaultdict


def load(path):
    rows = list(csv.DictReader(open(path)))
    keycols = ["conv", "qid"] if "conv" in rows[0] else ["qid"]
    by = defaultdict(dict)
    for r in rows:
        by[r["policy"]][tuple(r[c] for c in keycols)] = int(r["correct"])
    return by


def boot_ci(vals, n_boot=5000, seed=0):
    rng = random.Random(seed)
    N = len(vals)
    m = sum(vals) / N
    boots = sorted(sum(vals[rng.randrange(N)] for _ in range(N)) / N for _ in range(n_boot))
    return m, boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)]


def paired_diff_ci(diffs, n_boot=5000, seed=0):
    rng = random.Random(seed)
    N = len(diffs)
    m = sum(diffs) / N
    boots = sorted(sum(diffs[rng.randrange(N)] for _ in range(N)) / N for _ in range(n_boot))
    return m, boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)]


def mcnemar_p(b, c):
    """Exact two-sided binomial test on the b/c discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    cdf = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * cdf)


def main():
    path = sys.argv[1]
    by = load(path)
    print(f"\n=== {path.split('/')[-2]} ===")
    print(f"{'arm':<20}{'acc':>7}{'  95% CI':>18}{'n':>6}")
    for pol in sorted(by, key=lambda p: -sum(by[p].values()) / len(by[p])):
        vals = list(by[pol].values())
        m, lo, hi = boot_ci(vals)
        print(f"{pol:<20}{m:>7.2f}   [{lo:.2f}, {hi:.2f}]{len(vals):>6}")

    pairs = [a.split(":") for a in sys.argv[2:]]
    if pairs:
        print(f"\n{'comparison':<34}{'d_acc':>8}{'  95% CI':>18}{'McNemar p':>12}")
        for x, y in pairs:
            keys = sorted(set(by[x]) & set(by[y]))
            ax = [by[x][k] for k in keys]
            ay = [by[y][k] for k in keys]
            m, lo, hi = paired_diff_ci([ax[i] - ay[i] for i in range(len(keys))])
            b = sum(1 for i in range(len(keys)) if ax[i] > ay[i])
            c = sum(1 for i in range(len(keys)) if ax[i] < ay[i])
            p = mcnemar_p(b, c)
            print(f"{x + ' vs ' + y:<34}{m:>+8.2f}   [{lo:+.2f},{hi:+.2f}]{p:>11.4f}{'  *' if p < 0.05 else ''}")


if __name__ == "__main__":
    main()
