"""Generate brand QR codes for the deck.  python presentation/assets/gen_qr.py

Dark ink modules on white (brand, max scannability). Add LinkedIn once known.
"""
from pathlib import Path

import qrcode

OUT = Path(__file__).resolve().parent / "qr"
OUT.mkdir(parents=True, exist_ok=True)

LINKS = {
    "repo": "https://github.com/kanishkpatel1995/agent-harness",
    "newsletter": "https://learnagentic.substack.com",
    "x": "https://x.com/above_almighty",
    # "linkedin": "https://www.linkedin.com/in/<handle>",   # TODO: fill when provided
}

for name, url in LINKS.items():
    qr = qrcode.QRCode(border=1, box_size=16, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#2E2C32", back_color="white")
    img.save(OUT / f"qr_{name}.png")
    print("wrote", OUT / f"qr_{name}.png", "->", url)
