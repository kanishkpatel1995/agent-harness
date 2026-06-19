"""RunContext — the per-experiment run directory + manifest.

The protocol's unit of traceability. Creates

    experiments/runs/EXP-NNN__<slug>__<YYYYMMDD-HHMM>/
        manifest.yaml   hypothesis, assumptions, config, git sha, deps, python
        prompts.jsonl   every LLM call (written by NimLLM)
        results.csv     the measurements
        figures/        publication PDFs
        README.md       human summary (fill in after analysis)

so a stranger can open one folder and see exactly what was run, why, and how.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from .logsetup import get

log = get("run")

RUNS_DIR = Path("experiments/runs")


def _git_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def _dep_versions():
    out = {}
    for pkg in ("litellm", "matplotlib", "requests", "python-dotenv"):
        try:
            from importlib.metadata import version
            out[pkg] = version(pkg)
        except Exception:
            out[pkg] = "not-installed"
    return out


def _scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if "\n" in s or ":" in s or s.strip() != s:
        return '"' + s.replace('"', '\\"').replace("\n", " ") + '"'
    return s


def _yaml(obj, indent=0):
    """Tiny YAML emitter for the flat-ish manifest (no PyYAML dependency)."""
    pad = "  " * indent
    lines = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{pad}{k}:")
                lines.append(_yaml(v, indent + 1))
            else:
                lines.append(f"{pad}{k}: {_scalar(v)}")
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(_yaml(v, indent + 1))
            else:
                lines.append(f"{pad}- {_scalar(v)}")
    return "\n".join(lines)


class RunContext:
    def __init__(self, cfg):
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M")
        self.dir = RUNS_DIR / f"{cfg.exp_id}__{cfg.slug}__{stamp}"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir = self.dir / "figures"
        self.figures_dir.mkdir(exist_ok=True)
        self.results_path = self.dir / "results.csv"
        self.transcript_path = self.dir / "prompts.jsonl"
        self._write_manifest(cfg, stamp)
        log.info(f"run dir: {self.dir}")

    def _write_manifest(self, cfg, stamp):
        manifest = {
            "exp_id": cfg.exp_id,
            "slug": cfg.slug,
            "created_utc": stamp,
            "git_sha": _git_sha(),
            "python": sys.version.split()[0],
            "deps": _dep_versions(),
            "hypothesis": cfg.hypothesis,
            "assumptions": list(cfg.assumptions),
            "config": {k: (list(v) if isinstance(v, tuple) else v)
                       for k, v in asdict(cfg).items()},
        }
        (self.dir / "manifest.yaml").write_text(_yaml(manifest) + "\n", encoding="utf-8")
        (self.dir / "README.md").write_text(
            f"# {cfg.exp_id} — {cfg.slug}\n\n"
            f"**Hypothesis:** {cfg.hypothesis}\n\n"
            "**Assumptions:**\n" + "".join(f"- {a}\n" for a in cfg.assumptions) +
            f"\nRun `{stamp}` · git `{_git_sha()}` · model `{cfg.model}`\n\n"
            "## Results\n\n_Fill in after analysis: did the hypothesis hold? "
            "strongest threat?_\n",
            encoding="utf-8",
        )


def latest_results():
    """The most recent run's results.csv (run dirs sort chronologically by name)."""
    runs = sorted(RUNS_DIR.glob("EXP-*/results.csv"))
    return runs[-1] if runs else None
