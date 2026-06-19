"""One place to configure logging. Every module logs through a `bench.*` logger,
so the whole experiment narrates itself to the terminal.

  default        -> INFO  (one line per cell + per compaction event)
  -v             -> INFO
  -vv            -> DEBUG (one line per step: every read, token check, score, call)
"""

from __future__ import annotations

import logging
import sys


def setup(level: str = "INFO"):
    lvl = getattr(logging, str(level).upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-5s %(name)-13s | %(message)s", "%H:%M:%S")
    )
    root = logging.getLogger("bench")
    root.handlers[:] = [handler]   # replace, so repeated setup() doesn't double-log
    root.setLevel(lvl)
    root.propagate = False
    return root


def get(name: str) -> logging.Logger:
    """A child logger, e.g. get('window') -> 'bench.window'."""
    return logging.getLogger(f"bench.{name}")
