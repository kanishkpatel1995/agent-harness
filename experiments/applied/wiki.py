"""Fetch Wikipedia article plain text via the MediaWiki API, cached to disk.

Each article is capped so the window overflows a small budget without unbounded
cost. Caching makes re-runs free and deterministic.
"""

from __future__ import annotations

import hashlib
import urllib.parse
from pathlib import Path

import requests

from experiments.bench.logsetup import get

log = get("wiki")
CACHE = Path("experiments/applied/.wikicache")
CACHE.mkdir(parents=True, exist_ok=True)
CAP_CHARS = 6000  # lead + early sections; enough to overflow a small budget


def _title(url):
    return urllib.parse.unquote(url.rstrip("/").split("/wiki/")[-1]).replace("_", " ")


def fetch(url):
    key = hashlib.sha256(url.encode()).hexdigest()[:20]
    cp = CACHE / f"{key}.txt"
    if cp.exists():
        return cp.read_text(encoding="utf-8")
    title = _title(url)
    text = ""
    try:
        host = url.split("/wiki/")[0]
        r = requests.get(
            host + "/w/api.php",
            params={"action": "query", "prop": "extracts", "explaintext": 1,
                    "redirects": 1, "format": "json", "titles": title},
            headers={"User-Agent": "agent-harness-research/0.1 (research)"},
            timeout=30,
        )
        pages = r.json()["query"]["pages"]
        text = (next(iter(pages.values())).get("extract") or "")[:CAP_CHARS]
    except Exception as e:  # noqa: BLE001
        log.warning(f"fetch failed for {title!r}: {type(e).__name__}: {e}")
    cp.write_text(text, encoding="utf-8")
    log.debug(f"fetched {title!r}: {len(text)} chars")
    return text
