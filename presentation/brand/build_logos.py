"""Generate the comprehensive Founsi logo set from the horizontal lockup.

Source: founsi-logo-horizontal.svg (icon mark + "Founsi.ai" wordmark).
This derives every variant by recoloring / extracting paths, so the set stays
in sync with one source of truth. Run:

    python presentation/brand/build_logos.py
"""

from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "founsi-logo-horizontal.svg").read_text()

PURPLE = "#9378FF"
INK = "#2E2C32"
GREY = "#655E74"
WHITE = "#FFFFFF"

# Brand palette (also exported for charts, see chart_style.py)
PATHS = re.findall(r'<path\s+d="([^"]*)"\s+fill="([^"]*)"\s*/>', SRC)
MARK_PREFIXES = ("M126.215", "M47.1949", "M74.0172")  # the three icon-mark paths


def _is_mark(d):
    return any(d.startswith(p) for p in MARK_PREFIXES)


MARK = [(d, f) for d, f in PATHS if _is_mark(d)]
WORD = [(d, f) for d, f in PATHS if not _is_mark(d)]


def _paths(paths, recolor=None):
    return "\n".join(
        f'<path d="{d}" fill="{(recolor(f) if recolor else f)}"/>' for d, f in paths
    )


def _svg(viewbox, w, h, body, head=""):
    return (
        f'<svg width="{w}" height="{h}" viewBox="{viewbox}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg">\n{head}{body}\n</svg>\n'
    )


def _write(name, content):
    (HERE / name).write_text(content)
    print("wrote", name)


def _recolor_src(mapping):
    s = SRC
    for a, b in mapping.items():
        s = s.replace(a, b)
    return s


# --- full horizontal lockup, recolored variants ---------------------------
_write("founsi-logo-horizontal-primary.svg", _recolor_src({GREY: INK}))        # ink wordmark, light bg
_write("founsi-logo-horizontal-inverted.svg", _recolor_src({GREY: WHITE}))     # white wordmark, dark bg
_write("founsi-logo-horizontal-mono-black.svg", _recolor_src({PURPLE: INK, GREY: INK}))
_write("founsi-logo-horizontal-mono-white.svg", _recolor_src({PURPLE: WHITE, GREY: WHITE}))

# --- icon mark only -------------------------------------------------------
MARK_VB = "0 0 146 110"
_write("founsi-mark.svg", _svg(MARK_VB, 146, 110, _paths(MARK)))
_write("founsi-mark-inverted.svg", _svg(MARK_VB, 146, 110, _paths(MARK, lambda f: WHITE)))
_write("founsi-mark-mono-black.svg", _svg(MARK_VB, 146, 110, _paths(MARK, lambda f: INK)))

# --- wordmark only (ink letters + purple .ai) -----------------------------
_write("founsi-wordmark.svg", _svg("175 0 517 110", 517, 110,
       _paths(WORD, lambda f: INK if f == GREY else f)))

# --- app icons: mark centered in a rounded square -------------------------
def _app_icon(bg, mark_fill, head_extra=""):
    g = f'<g transform="translate(117,151) scale(1.9)">\n{_paths(MARK, lambda f: mark_fill)}\n</g>'
    head = f'<rect width="512" height="512" rx="114" fill="{bg}"/>\n{head_extra}'
    return _svg("0 0 512 512", 512, 512, g, head=head)


_write("founsi-app-icon.svg", _app_icon(PURPLE, WHITE))
_write("founsi-app-icon-light.svg", _app_icon(
    WHITE, PURPLE,
    head_extra='<rect x="1" y="1" width="510" height="510" rx="113" fill="none" '
               'stroke="#9378FF" stroke-opacity="0.15"/>\n'))

# --- favicon: tight square mark -------------------------------------------
_write("founsi-favicon.svg", _svg("0 -18 146 146", 64, 64, _paths(MARK)))

print(f"\n{len(PATHS)} source paths -> {len(MARK)} mark, {len(WORD)} wordmark")
print("Logo set complete.")
