"""Rate-limited, cached client for NVIDIA NIM (free tier) via litellm.

Free tier = ~40 req/min, hard, with no raise-on-request. So every call here is:
  - PACED   : never faster than min_interval apart (1.6s => <=37/min, under 40).
  - RETRIED : 429 / 5xx / timeouts get exponential backoff + jitter, honoring
              Retry-After when litellm surfaces it.
  - CACHED  : identical (model, temp, messages) calls are served from disk, so
              re-running the bake-off costs zero new requests (idempotent).

litellm reads the key from NVIDIA_NIM_API_KEY; your .env names it
NVIDIA_FREE_API_KEY, so we map one to the other once, here.
"""

from __future__ import annotations

import concurrent.futures
import datetime
import hashlib
import json
import logging
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("bench.model")


def _completion_with_deadline(model, messages, temperature, soft_timeout, hard_timeout):
    """Call litellm.completion with a hard wall-clock deadline.

    litellm's own ``timeout`` is not reliably enforced for the nvidia_nim transport:
    if the server accepts the connection then holds it open without sending bytes, the
    read timeout can fail to fire and the call wedges forever (observed at 0% CPU with
    no error). We run the call on a worker thread and bound it with
    ``future.result(timeout=...)`` so a wedged socket raises instead of hanging the
    whole sweep. The orphaned thread is abandoned (Python cannot kill it) and will die
    when its connection eventually drops; that is acceptable for a bounded dev run.
    """
    import litellm

    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        fut = ex.submit(litellm.completion, model=model, messages=messages,
                        temperature=temperature, timeout=soft_timeout)
        return fut.result(timeout=hard_timeout)
    except concurrent.futures.TimeoutError:
        raise TimeoutError(f"hard watchdog: no response in {hard_timeout}s "
                           "(litellm ignored its own timeout)")
    finally:
        ex.shutdown(wait=False)


def _load_env_key():
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    key = os.environ.get("NVIDIA_FREE_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY")
    if key:
        os.environ["NVIDIA_NIM_API_KEY"] = key  # litellm looks here
    return key


@dataclass
class NimResult:
    content: str
    usage: dict  # {"prompt_tokens", "completion_tokens"}
    cached: bool = False


class NimLLM:
    def __init__(self, model="meta/llama-3.3-70b-instruct", *, temperature=0.2,
                 min_interval=1.6, max_retries=6, cache_dir="experiments/.cache",
                 transcript_path=None):
        self.model = model if model.startswith("nvidia_nim/") else f"nvidia_nim/{model}"
        self.temperature = temperature
        self.min_interval = min_interval
        self.max_retries = max_retries
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        # Per-run transcript of every prompt + response (the protocol's record).
        self.transcript = Path(transcript_path) if transcript_path else None
        if self.transcript:
            self.transcript.parent.mkdir(parents=True, exist_ok=True)
        self._last = 0.0
        key = _load_env_key()
        if not key:
            raise RuntimeError("No NVIDIA key found. Put NVIDIA_FREE_API_KEY in .env")
        self._key = key

    # --- pacing: never exceed ~37/min --------------------------------------
    def _pace(self):
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    # --- cache key ----------------------------------------------------------
    def _ckey(self, messages):
        blob = json.dumps([self.model, self.temperature, messages], sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode()).hexdigest()[:24]

    # --- the call -----------------------------------------------------------
    def complete(self, messages, stage="call"):
        ck = self._ckey(messages)
        cp = self.cache / f"{ck}.json"
        if cp.exists():
            d = json.loads(cp.read_text())
            log.debug(f"cache hit {ck[:8]} ({self.model})")
            res = NimResult(d["content"], d["usage"], cached=True)
            self._record(stage, messages, res)
            return res

        last = None
        for attempt in range(self.max_retries):
            self._pace()
            try:
                r = _completion_with_deadline(self.model, messages, self.temperature,
                                              soft_timeout=60, hard_timeout=75)
                m = r.choices[0].message
                usage = {
                    "prompt_tokens": getattr(r.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(r.usage, "completion_tokens", 0),
                }
                d = {"content": m.content or "", "usage": usage}
                cp.write_text(json.dumps(d, ensure_ascii=False))
                log.debug(f"live call {self.model}: in={usage['prompt_tokens']} "
                          f"out={usage['completion_tokens']}, latency={time.monotonic() - self._last:.1f}s")
                res = NimResult(d["content"], usage, cached=False)
                self._record(stage, messages, res)
                return res
            except Exception as e:  # noqa: BLE001 — we classify below
                last = e
                if not _retryable(e) or attempt == self.max_retries - 1:
                    raise
                s = _backoff(e, attempt)
                log.warning(f"retry {attempt + 1}/{self.max_retries} after {type(e).__name__}; sleeping {s:.1f}s")
                time.sleep(s)
        raise last

    def _record(self, stage, messages, res):
        """Append the full prompt + response to the run transcript (if set) — the
        human-readable, per-run record the protocol requires."""
        if not self.transcript:
            return
        rec = {
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "stage": stage, "model": self.model, "cached": res.cached,
            "messages": messages, "response": res.content, "usage": res.usage,
        }
        with self.transcript.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def count_tokens(self, messages):
        try:
            import litellm

            return litellm.token_counter(model=self.model, messages=messages)
        except Exception:
            return sum(max(1, len(str(m)) // 4) for m in messages)

    # --- read-only catalog --------------------------------------------------
    def list_models(self):
        import requests

        r = requests.get(
            "https://integrate.api.nvidia.com/v1/models",
            headers={"Authorization": f"Bearer {self._key}"},
            timeout=30,
        )
        r.raise_for_status()
        return sorted(m["id"] for m in r.json().get("data", []))


def _retryable(e):
    s = (str(e) + type(e).__name__).lower()
    return any(x in s for x in (
        "429", "ratelimit", "rate limit", "timeout", "502", "503", "504",
        "overloaded", "connection", "apiconnection",
    ))


def _backoff(e, attempt, base=2.0, cap=45.0):
    ra = getattr(e, "retry_after", None)
    if ra:
        try:
            return min(cap, float(ra))
        except Exception:
            pass
    return min(cap, base * (2 ** attempt)) + random.uniform(0, 1.0)
