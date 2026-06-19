"""Fetch Wikipedia article plain text via the MediaWiki API, cached to disk.

Robustness matters here: Wikipedia rejects unpaced bursts and thin User-Agents,
so we pace requests, send a descriptive UA with a contact URL (per Wikipedia's
API etiquette), retry with backoff, and never cache an empty failure. Each article
is capped so the window overflows a small budget without unbounded cost. Caching
makes re-runs free and deterministic; oracle retrieval (the gold articles) isolates
compaction from search quality.
"""

from __future__ import annotations

import hashlib
import random
import time
import urllib.parse
from pathlib import Path

import requests

from experiments.bench.logsetup import get

log = get("wiki")
CACHE = Path("experiments/applied/.wikicache")
CACHE.mkdir(parents=True, exist_ok=True)
CAP_CHARS = 6000
UA = ("agent-harness/0.1 (https://github.com/kanishkpatel1995/agent-harness; "
      "context-compaction research) python-requests")
MIN_INTERVAL = 0.4  # polite pacing between requests
_last = [0.0]


def _title(url):
    return urllib.parse.unquote(url.rstrip("/").split("/wiki/")[-1]).split("#")[0].replace("_", " ")


def _pace():
    wait = MIN_INTERVAL - (time.monotonic() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.monotonic()


def fetch(url):
    key = hashlib.sha256(url.encode()).hexdigest()[:20]
    cp = CACHE / f"{key}.txt"
    if cp.exists():
        cached = cp.read_text(encoding="utf-8")
        if cached.strip():
            return cached  # ignore empty cache entries and re-fetch

    title = _title(url)
    host = url.split("/wiki/")[0]
    api = host + "/w/api.php"
    params = {"action": "query", "prop": "extracts", "explaintext": 1,
              "redirects": 1, "format": "json", "titles": title}

    for attempt in range(4):
        _pace()
        try:
            r = requests.get(api, params=params, headers={"User-Agent": UA}, timeout=30)
            if r.status_code == 200 and r.text.strip():
                pages = r.json().get("query", {}).get("pages", {})
                text = (next(iter(pages.values())).get("extract") or "")[:CAP_CHARS] if pages else ""
                if text.strip():
                    cp.write_text(text, encoding="utf-8")
                    log.debug(f"fetched {title!r}: {len(text)} chars")
                    return text
            log.debug(f"fetch {title!r} attempt {attempt + 1}: status={r.status_code} len={len(r.text)}")
        except Exception as e:  # noqa: BLE001
            log.debug(f"fetch {title!r} attempt {attempt + 1} error: {type(e).__name__}: {e}")
        time.sleep(0.6 * (attempt + 1) + random.random())

    log.warning(f"fetch failed for {title!r} after retries (not cached)")
    return ""
