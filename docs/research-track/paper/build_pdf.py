#!/usr/bin/env python3
"""Build the paper PDF from draft.md.

Uses pypandoc (bundled pandoc) + xelatex. xelatex is chosen over pdflatex so the middle-dot
separators in the references and any future Unicode render without an inputenc workaround, and so
the body font matches the figures' Times New Roman house style (TeX Gyre Termes is a Times clone
that ships with MacTeX/TeX Live). Figures are embedded as PDFs; image paths in draft.md are
root-relative, so this script runs pandoc from the repo root.

    python docs/research-track/paper/build_pdf.py        # -> draft.pdf next to draft.md
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]   # paper -> research-track -> docs -> repo root
DRAFT = REPO / "docs" / "research-track" / "paper" / "draft.md"
OUT = DRAFT.with_name("draft.pdf")

EXTRA = [
    "--pdf-engine=xelatex",
    "--resource-path", str(REPO),          # resolve root-relative figure paths
    "-V", "geometry:margin=1in",
    "-V", "fontsize=11pt",
    "-V", "mainfont=Times New Roman",      # matches figstyle.py's house font
    "-V", "linkcolor=RoyalBlue",
    "-V", "urlcolor=RoyalBlue",
    "-V", "colorlinks=true",
]


def main() -> int:
    import pypandoc

    os.chdir(REPO)                          # so root-relative image paths resolve
    print(f"pandoc {pypandoc.get_pandoc_version()} -> xelatex")
    print(f"in:  {DRAFT.relative_to(REPO)}")
    pypandoc.convert_file(str(DRAFT), "pdf", outputfile=str(OUT), extra_args=EXTRA)
    size = OUT.stat().st_size
    print(f"out: {OUT.relative_to(REPO)}  ({size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
