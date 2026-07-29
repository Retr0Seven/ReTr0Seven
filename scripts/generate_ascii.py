#!/usr/bin/env python3
"""Generate the animated ASCII logo used by the profile README.

Usage:
    python scripts/generate_ascii.py assets/avatar-source.jpg ascii.svg

Requires Pillow. The generated SVG has no external font or image dependency.
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

WIDTH = 620
HEIGHT = 500
COLS = 84
CHARACTER_ASPECT = 0.50
FONT_SIZE = 8.2
ROW_HEIGHT = 8.4
LOGO_WIDTH = 382
LOGO_TOP = 44


def ascii_rows(source: Path) -> list[str]:
    image = Image.open(source).convert("L")
    image = ImageOps.autocontrast(image)
    # The source is line art. A small max filter preserves thin strokes after
    # downsampling without turning the black background into visual noise.
    image = image.filter(ImageFilter.MaxFilter(5))
    rows = max(1, int(COLS * image.height / image.width * CHARACTER_ASPECT))
    image = image.resize((COLS, rows), Image.Resampling.BILINEAR)

    output: list[str] = []
    for y in range(rows):
        chars: list[str] = []
        for x in range(COLS):
            value = image.getpixel((x, y))
            if value > 105:
                char = "@"
            elif value > 65:
                char = "+"
            elif value > 38:
                char = "·"
            else:
                char = " "
            chars.append(char)
        output.append("".join(chars))
    return output


def build_svg(rows: list[str]) -> str:
    x = (WIDTH - LOGO_WIDTH) / 2
    total_logo_height = len(rows) * ROW_HEIGHT
    title_y = max(LOGO_TOP + total_logo_height + 29, 407)
    subtitle_y = title_y + 24

    defs: list[str] = [
        "<defs>",
        '<linearGradient id="ink" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0" stop-color="#67e8f9"/>',
        '<stop offset="0.55" stop-color="#7ee787"/>',
        '<stop offset="1" stop-color="#a7f3d0"/>',
        "</linearGradient>",
        '<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">',
        '<path d="M24 0H0V24" fill="none" stroke="#173242" stroke-width="0.55" opacity="0.32"/>',
        "</pattern>",
        '<filter id="glow" x="-30%" y="-30%" width="160%" height="160%">',
        '<feGaussianBlur stdDeviation="1.15" result="blur"/>',
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
        "</filter>",
    ]

    body: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        *defs,
    ]

    for index in range(len(rows)):
        y = LOGO_TOP + index * ROW_HEIGHT
        delay = 0.10 + index * 0.055
        defs.append(
            f'<clipPath id="row-{index}"><rect x="{x:.2f}" y="{y - FONT_SIZE:.2f}" '
            f'width="0" height="{ROW_HEIGHT + 2:.2f}">'
            f'<animate attributeName="width" from="0" to="{LOGO_WIDTH:.2f}" '
            f'begin="{delay:.3f}s" dur="0.36s" fill="freeze"/>'
            "</rect></clipPath>"
        )
    defs.append("</defs>")

    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        *defs,
        '<rect x="1" y="1" width="618" height="468" rx="16" fill="#05090f" stroke="#1c3444" stroke-width="2"/>',
        '<rect x="12" y="12" width="596" height="446" rx="11" fill="url(#grid)"/>',
        '<circle cx="27" cy="27" r="4" fill="#ff6b6b" opacity="0.78"/>',
        '<circle cx="41" cy="27" r="4" fill="#f6c85f" opacity="0.78"/>',
        '<circle cx="55" cy="27" r="4" fill="#7ee787" opacity="0.78"/>',
        '<text x="310" y="31" text-anchor="middle" fill="#6f8190" font-size="10" '
        'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" letter-spacing="1.4">retr0seven://identity</text>',
        '<line x1="18" y1="40" x2="602" y2="40" stroke="#193242"/>',
        '<g fill="#67e8f9" opacity="0.16" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="{FONT_SIZE}" font-weight="600">',
    ]

    for index, row in enumerate(rows):
        y = LOGO_TOP + index * ROW_HEIGHT
        safe = html.escape(row)
        body.append(
            f'<text xml:space="preserve" x="{x:.2f}" y="{y:.2f}" '
            f'textLength="{LOGO_WIDTH:.2f}" lengthAdjust="spacingAndGlyphs">{safe}</text>'
        )
    body.extend([
        "</g>",
        '<g fill="url(#ink)" filter="url(#glow)" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="{FONT_SIZE}" font-weight="600">',
    ])

    for index, row in enumerate(rows):
        y = LOGO_TOP + index * ROW_HEIGHT
        safe = html.escape(row)
        body.append(
            f'<text xml:space="preserve" x="{x:.2f}" y="{y:.2f}" '
            f'textLength="{LOGO_WIDTH:.2f}" lengthAdjust="spacingAndGlyphs" '
            f'clip-path="url(#row-{index})">{safe}</text>'
        )
    body.extend(
        [
            "</g>",
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="2.65s" dur="0.55s" fill="freeze"/>',
            f'<text x="34" y="{title_y:.1f}" fill="#7ee787" font-size="13" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">mouad@retr0seven:~$ whoami</text>',
            f'<text x="34" y="{subtitle_y:.1f}" fill="#f0f6fc" font-size="17" font-weight="600" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">Mouad Hassari</text>',
            f'<text x="34" y="{subtitle_y + 20:.1f}" fill="#9aa9b7" font-size="11.5" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">IT-Specialist | Senior Computer Science Student @AUI</text>',
            f'<rect x="{WIDTH - 42}" y="{subtitle_y + 9:.1f}" width="8" height="14" fill="#67e8f9"><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>',
            "</g>",
            "</svg>",
        ]
    )
    return "".join(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(build_svg(ascii_rows(args.source)), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
