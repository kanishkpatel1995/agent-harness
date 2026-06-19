"""Pre-fetch FRAMES gold Wikipedia articles into the cache so larger runs start
without a long fetch phase. Hits Wikipedia only (no model API), so it is safe to
run alongside an experiment that is using the model.

    python experiments/applied/precache.py 150
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from experiments.bench.logsetup import setup, get
from experiments.applied import frames, wiki

log = get("precache")


def main():
    setup("INFO")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    items = frames.load(n, 0)
    fetched = 0
    for it in items:
        for u in it.wiki_urls[:6]:
            if wiki.fetch(u).strip():
                fetched += 1
    log.info(f"pre-fetched articles for {len(items)} FRAMES questions; {fetched} non-empty cached")


if __name__ == "__main__":
    main()
