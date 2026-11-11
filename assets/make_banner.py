"""Genera el banner PNG (assets/banner.png) a partir del SVG del proyecto.

Requiere Pillow. Es opcional: el SVG ya sirve para el README.
    python assets/make_banner.py
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    print("Pillow no disponible: instalar con 'pip install pillow'")
    sys.exit(0)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "banner.png"
W, H = 1280, 400


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                continue
    return ImageFont.load_default()


def main() -> int:
    image = Image.new("RGB", (W, H), (11, 31, 51))
    draw = ImageDraw.Draw(image)

    # degradado diagonal
    for x in range(W):
        t = x / W
        r = int(11 + (14 - 11) * t)
        g = int(31 + (124 - 31) * t)
        b = int(51 + (123 - 51) * t)
        draw.line([(x, 0), (x, H)], fill=(r, g, b))

    # bloque isometrico
    def iso(origin_x, origin_y, color):
        top = [(origin_x, origin_y + 40), (origin_x + 40, origin_y + 18), (origin_x + 80, origin_y + 40), (origin_x + 40, origin_y + 62)]
        left = [(origin_x, origin_y + 40), (origin_x, origin_y + 92), (origin_x + 40, origin_y + 114), (origin_x + 40, origin_y + 62)]
        right = [(origin_x + 80, origin_y + 40), (origin_x + 80, origin_y + 92), (origin_x + 40, origin_y + 114), (origin_x + 40, origin_y + 62)]
        draw.polygon(left, fill=(9, 26, 43), outline=color)
        draw.polygon(right, fill=(13, 45, 66), outline=color)
        draw.polygon(top, fill=(16, 60, 86), outline=color)

    iso(70, 236, (79, 209, 197))
    iso(130, 216, (99, 179, 237))

    draw.text((250, 118), "GeoLogistix", font=font(76, bold=True), fill=(255, 255, 255))
    draw.text((252, 208), "Comparador auditable de costo entregado", font=font(27, bold=True), fill=(79, 209, 197))
    draw.text((252, 254), "Material + flete + ajustes · Conversión FX fechada · Procedencia por dato", font=font(19), fill=(199, 214, 227))
    draw.text((252, 284), "Determinista · Sin IA · No inventa datos · Decisión humana", font=font(19), fill=(199, 214, 227))

    chips = [("delivered-cost/0.1", 228), ("observed | estimated", 188), ("MIT · 0 deps", 176)]
    x = 252
    for label, width in chips:
        draw.rounded_rectangle([x, 318, x + width, 350], radius=6, fill=(9, 26, 43), outline=(79, 209, 197))
        draw.text((x + 14, 326), label, font=font(16), fill=(230, 255, 250))
        x += width + 12

    image.save(OUT, "PNG", optimize=True)
    print(f"[ok] {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
