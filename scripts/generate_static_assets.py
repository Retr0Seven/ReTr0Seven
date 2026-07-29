#!/usr/bin/env python3
"""Generate the static heading and stack SVG assets."""
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 620
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
STYLE = """
<style>
.h{fill:#24292f}.line{stroke:#d0d7de}.tag{fill:#f6f8fa;stroke:#d0d7de}.t{fill:#57606a}.blue{fill:#0969da}
@media(prefers-color-scheme:dark){.h{fill:#f0f6fc}.line{stroke:#30363d}.tag{fill:#0d1117;stroke:#30363d}.t{fill:#c9d1d9}.blue{fill:#58a6ff}}
</style>
"""


def heading(filename: str, title: str) -> None:
    # Approximate monospace heading width: 8 px per glyph at 15px/600.
    line_start = 22 + len(title) * 9
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="38" viewBox="0 0 {WIDTH} 38" '
        f'font-family="{MONO}">{STYLE}'
        f'<text x="0" y="25" class="h" font-size="15" font-weight="600">{escape(title)}</text>'
        f'<line x1="{line_start}" y1="20" x2="620" y2="20" class="line"/>'
        '</svg>'
    )
    (ROOT / filename).write_text(svg, encoding="utf-8")


def stack() -> None:
    rows = [
        ["TypeScript", "Next.js", "React", "PostgreSQL", "Prisma", "Tailwind", "Zod"],
        ["Recharts", "Vercel", "Neon", "Linux", "Networking", "Cybersecurity"],
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="82" viewBox="0 0 {WIDTH} 82" '
        f'font-family="{MONO}">{STYLE}'
    ]
    for row_index, row in enumerate(rows):
        x = 0
        y = 8 + row_index * 38
        for label in row:
            width = 18 + len(label) * 7.1
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="26" rx="4" class="tag"/>')
            parts.append(f'<text x="{x + 9:.1f}" y="{y + 17}" class="t" font-size="10.5">{escape(label)}</text>')
            x += width + 7
    parts.append('</svg>')
    (ROOT / "stack.svg").write_text("".join(parts), encoding="utf-8")


for filename, title in [
    ("hd-about.svg", "about"),
    ("hd-stack.svg", "stack"),
    ("hd-projects.svg", "projects"),
    ("hd-stats.svg", "stats"),
    ("hd-about-this-page.svg", "about this page"),
]:
    heading(filename, title)
stack()
