"""Tool registry: what the agent can DO.

If the ContextManager is what the agent knows, this is what it can do. Each
tool is a plain Python function plus a JSON schema the model sees. Dispatch is
a dict lookup. Keeping this boring and explicit is a feature: you can read
exactly what the agent is allowed to touch.

The `finish` tool is special and handled in loop.py — it's how the agent says
"I'm done, here's the report."
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import web  # noqa: E402  (the tools/ package, not this module)


class ToolRegistry:
    def __init__(self, scratchpad):
        self.scratchpad = scratchpad
        self._tools = {
            "web_search": self._web_search,
            "fetch_url": self._fetch_url,
            "save_note": self._save_note,
            "read_notes": self._read_notes,
        }

    # --- dispatch -----------------------------------------------------------
    def dispatch(self, name: str, args: dict) -> str:
        fn = self._tools.get(name)
        if not fn:
            return f"ERROR: unknown tool {name!r}. Available: {list(self._tools)}"
        try:
            return fn(**args)
        except TypeError as exc:
            return f"ERROR calling {name}: {exc}"

    # --- the tools ----------------------------------------------------------
    def _web_search(self, query: str, k: int = 4) -> str:
        return web.web_search(query, k=k)

    def _fetch_url(self, url: str) -> str:
        return web.fetch_url(url)

    def _save_note(self, text: str, tag: str = "finding") -> str:
        return self.scratchpad.save_note(text, tag=tag)

    def _read_notes(self) -> str:
        return self.scratchpad.read_notes()

    # --- schemas the model sees --------------------------------------------
    def schemas(self) -> list:
        return [
            _fn(
                "web_search",
                "Search the web for a query. Returns titles, URLs, and snippets.",
                {"query": _str("Search query"), "k": _int("How many results (default 4)")},
                ["query"],
            ),
            _fn(
                "fetch_url",
                "Fetch the readable text of a URL found via web_search.",
                {"url": _str("The URL to fetch")},
                ["url"],
            ),
            _fn(
                "save_note",
                "Save a finding to the scratchpad (memory that lives OUTSIDE the "
                "context window). Use this for every fact worth keeping so it "
                "survives compaction.",
                {"text": _str("The finding to remember"), "tag": _str("Short label, e.g. 'finding'")},
                ["text"],
            ),
            _fn(
                "read_notes",
                "Read everything saved to the scratchpad so far. Use before "
                "writing the final report.",
                {},
                [],
            ),
            _fn(
                "finish",
                "Finish the task and return the final report. Call this exactly "
                "once when research is complete.",
                {"report": _str("The complete final report, in markdown")},
                ["report"],
            ),
        ]


# --- tiny schema helpers ---------------------------------------------------
def _fn(name, desc, props, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {"type": "object", "properties": props, "required": required},
        },
    }


def _str(desc):
    return {"type": "string", "description": desc}


def _int(desc):
    return {"type": "integer", "description": desc}
