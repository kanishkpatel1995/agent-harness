"""Web tools: search + fetch.

Two modes:
  - OFFLINE (default, HARNESS_OFFLINE=1): deterministic results from the
    fixtures in this folder, plus generated long-form pages. The whole demo
    runs with no network and no API keys — which is exactly what you want when
    you're live on stage on conference wifi.
  - ONLINE (HARNESS_OFFLINE=0): a thin real implementation using DuckDuckGo +
    requests. Good enough to play with; swap in Tavily/Brave/SerpAPI for real
    research quality (see docs/references.md).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _offline() -> bool:
    return os.environ.get("HARNESS_OFFLINE", "1") != "0"


# --- search ----------------------------------------------------------------
def web_search(query: str, k: int = 4) -> str:
    if _offline():
        results = _offline_search(query, k)
    else:
        results = _online_search(query, k)
    lines = [f"Search results for {query!r}:"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}\n   {r['url']}\n   {r['snippet']}")
    return "\n".join(lines)


def _offline_search(query: str, k: int) -> list[dict]:
    index = json.loads((FIXTURES / "index.json").read_text(encoding="utf-8"))
    # Rank fixtures by naive keyword overlap so results feel query-dependent.
    terms = {t.lower() for t in query.split()}
    scored = []
    for entry in index:
        hay = (entry["title"] + " " + entry["snippet"] + " " + entry.get("tags", "")).lower()
        score = sum(1 for t in terms if t in hay)
        scored.append((score, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:k]]


def _online_search(query: str, k: int) -> list[dict]:
    try:
        import requests
    except ImportError:
        return [{"title": "requests not installed", "url": "", "snippet": "pip install requests"}]
    resp = requests.get(
        "https://duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": "Mozilla/5.0 (agent-harness demo)"},
        timeout=15,
    )
    import re

    hits = re.findall(r'result__a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text)
    out = []
    for url, title in hits[:k]:
        out.append({"title": re.sub("<.*?>", "", title), "url": url, "snippet": ""})
    return out or [{"title": "no results", "url": "", "snippet": ""}]


# --- fetch -----------------------------------------------------------------
def fetch_url(url: str) -> str:
    if _offline():
        return _offline_fetch(url)
    return _online_fetch(url)


def _offline_fetch(url: str) -> str:
    index = json.loads((FIXTURES / "index.json").read_text(encoding="utf-8"))
    for entry in index:
        if entry["url"] == url:
            body = (FIXTURES / entry["file"]).read_text(encoding="utf-8")
            return body
    # Unknown URL: synthesize a long, deterministic page so the agent still has
    # something substantial to read (and the context fills up realistically).
    return _synthetic_page(url)


def _online_fetch(url: str) -> str:
    try:
        import requests
    except ImportError:
        return "requests not installed (pip install requests)"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (agent-harness demo)"}, timeout=20)
    text = resp.text
    try:
        from bs4 import BeautifulSoup

        text = BeautifulSoup(text, "html.parser").get_text("\n")
    except ImportError:
        pass
    return text[:8000]


def _synthetic_page(url: str) -> str:
    seed = int(hashlib.sha256(url.encode()).hexdigest(), 16)
    topic = url.rstrip("/").split("/")[-1].replace("-", " ") or "the topic"
    paras = []
    for i in range(8):
        n = (seed >> (i * 3)) % 5
        paras.append(
            f"Section {i + 1}. Regarding {topic}, sources broadly agree on several points. "
            f"Practitioners report that approach {n} tends to matter more than tooling choice. "
            "There are documented trade-offs around latency, cost, and reliability that recur "
            "across independent write-ups, and a few contested claims that are not yet settled. "
            "Concrete figures vary by setup but the direction of the effect is consistent."
        )
    return f"# {topic.title()}\n\n" + "\n\n".join(paras)
