#!/usr/bin/env python3
"""Generate the self-hosted SVG graphics used by the Retr0Seven profile README.

The scheduled workflow uses GitHub's GraphQL API and writes:
  hero.svg         animated ASCII portrait + contribution telemetry
  stats-panel.svg  streaks, languages, and a 90-day activity map

No third-party card service is used. The script depends only on Python's
standard library. Run with --demo to render the included local preview data.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
API = "https://api.github.com/graphql"
LOGIN = os.getenv("GH_LOGIN", "Retr0Seven")
TOKEN = os.getenv("GITHUB_TOKEN", "")
WIDTH = 620
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date weekday } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes {
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

STYLE = """
<style>
  .ink{fill:#57606a}.emph{fill:#24292f}.dim{fill:#6e7781}.blue{fill:#0969da}
  .rule{stroke:#d0d7de}.soft{fill:#afb8c1}.cell0{fill:#ebedf0}
  .cell1{fill:#9be9a8}.cell2{fill:#40c463}.cell3{fill:#30a14e}.cell4{fill:#216e39}
  @media(prefers-color-scheme:dark){
    .ink{fill:#c9d1d9}.emph{fill:#f0f6fc}.dim{fill:#8b949e}.blue{fill:#58a6ff}
    .rule{stroke:#30363d}.soft{fill:#484f58}.cell0{fill:#161b22}
    .cell1{fill:#0e4429}.cell2{fill:#006d32}.cell3{fill:#26a641}.cell4{fill:#39d353}
  }
</style>
"""


def utc_window() -> tuple[str, str]:
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=364)
    return f"{start.isoformat()}T00:00:00Z", f"{today.isoformat()}T23:59:59Z"


def fetch() -> dict:
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN is required unless --demo is used")
    start, end = utc_window()
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN, "from": start, "to": end}}).encode()
    request = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": f"{LOGIN}-profile-readme",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise SystemExit(f"GitHub GraphQL error: {payload['errors']}")
    user = (payload.get("data") or {}).get("user")
    if not user:
        raise SystemExit(f"GitHub user not found: {LOGIN}")
    return summarise_graphql(user)


def summarise_graphql(user: dict) -> dict:
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    counts = {day["date"]: int(day["contributionCount"]) for day in days}
    repos = user["repositories"]["nodes"]
    language_bytes: dict[str, int] = {}
    for repo in repos:
        for edge in (repo.get("languages") or {}).get("edges") or []:
            name = edge["node"]["name"]
            language_bytes[name] = language_bytes.get(name, 0) + int(edge["size"])
    ranked = sorted(language_bytes.items(), key=lambda item: (-item[1], item[0]))[:5]
    return build_summary(
        total=int(calendar["totalContributions"]),
        counts=counts,
        languages=ranked,
        as_of=max(counts) if counts else datetime.now(timezone.utc).date().isoformat(),
    )


def load_demo() -> dict:
    payload = json.loads((ASSETS / "demo-data.json").read_text(encoding="utf-8"))
    return build_summary(
        total=int(payload["total"]),
        counts={key: int(value) for key, value in payload["counts"].items()},
        languages=[(name, int(value)) for name, value in payload["languages"]],
        as_of=payload["as_of"],
    )


def build_summary(total: int, counts: dict[str, int], languages: list[tuple[str, int]], as_of: str) -> dict:
    end = date.fromisoformat(as_of)
    start = end - timedelta(days=364)
    days = [(start + timedelta(days=index), counts.get((start + timedelta(days=index)).isoformat(), 0)) for index in range(365)]
    active = sum(1 for _, value in days if value > 0)

    weekly: list[int] = []
    cursor = start
    while cursor <= end:
        week_end = min(cursor + timedelta(days=6), end)
        weekly.append(sum(counts.get((cursor + timedelta(days=i)).isoformat(), 0) for i in range((week_end - cursor).days + 1)))
        cursor = week_end + timedelta(days=1)

    current_length = 0
    current_start = None
    cursor = end
    while cursor >= start and counts.get(cursor.isoformat(), 0) > 0:
        current_length += 1
        current_start = cursor
        cursor -= timedelta(days=1)

    longest_length = 0
    longest_start = None
    longest_end = None
    run_length = 0
    run_start = None
    for day_value, contribution_count in days:
        if contribution_count > 0:
            if run_length == 0:
                run_start = day_value
            run_length += 1
            if run_length > longest_length:
                longest_length = run_length
                longest_start = run_start
                longest_end = day_value
        else:
            run_length = 0
            run_start = None

    total_language = sum(value for _, value in languages) or 1
    language_percentages = [(name, value / total_language * 100) for name, value in languages[:5]]

    return {
        "total": total,
        "active": active,
        "best_week": max(weekly) if weekly else 0,
        "weekly": weekly,
        "counts": counts,
        "as_of": end,
        "current": {"length": current_length, "start": current_start, "end": end if current_length else None},
        "longest": {"length": longest_length, "start": longest_start, "end": longest_end},
        "languages": language_percentages,
    }


def svg_open(height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="{MONO}">{STYLE}'
    )


def fmt_range(item: dict) -> str:
    if not item.get("start") or not item.get("end"):
        return "no active streak"
    start = item["start"]
    end = item["end"]
    return f"{start.strftime('%b').lower()} {start.day} - {end.strftime('%b').lower()} {end.day}"


def sparkline(values: list[int], x: float, y: float, width: float, height: float) -> str:
    values = values or [0]
    peak = max(values) or 1
    if len(values) == 1:
        points = [(x, y + height / 2)]
    else:
        points = [
            (x + index * width / (len(values) - 1), y + height - (value / peak) * height)
            for index, value in enumerate(values)
        ]
    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
    fill = f"{x:.1f},{y + height:.1f} {line} {x + width:.1f},{y + height:.1f}"
    return (
        f'<polygon points="{fill}" class="soft" opacity=".18"/>'
        f'<polyline points="{line}" fill="none" class="rule" stroke-width="1.6" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{points[-1][0]:.1f}" cy="{points[-1][1]:.1f}" r="3.2" class="emph"/>'
    )


def render_hero(summary: dict) -> str:
    portrait_path = ASSETS / "ascii-portrait.png"
    portrait_data = base64.b64encode(portrait_path.read_bytes()).decode("ascii")
    height = 730
    parts = [svg_open(height)]
    parts.append('<text x="20" y="28" font-size="11" font-weight="600"><tspan class="blue">retr0seven</tspan><tspan class="dim"> / README.md</tspan></text>')

    portrait_x = 34
    portrait_y = 42
    portrait_w = 552
    portrait_h = 420
    stripe_h = 8
    stripe_count = math.ceil(portrait_h / stripe_h)
    parts.append(
        f'<defs><image id="portrait" href="data:image/png;base64,{portrait_data}" '
        f'x="{portrait_x}" y="{portrait_y}" width="{portrait_w}" height="{portrait_h}" '
        f'preserveAspectRatio="xMidYMid meet"/></defs>'
    )
    duration = 0.075
    for index in range(stripe_count):
        y = portrait_y + index * stripe_h
        begin = index * duration
        clip_id = f"stripe{index}"
        parts.append(
            f'<clipPath id="{clip_id}"><rect x="{portrait_x}" y="{y}" width="0" height="{stripe_h + 1}">'
            f'<animate attributeName="width" from="0" to="{portrait_w}" begin="{begin:.2f}s" dur=".075s" fill="freeze"/>'
            f'</rect></clipPath><g clip-path="url(#{clip_id})"><use href="#portrait"/></g>'
        )

    reveal_end = stripe_count * duration + 0.15
    parts.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{reveal_end:.2f}s" dur=".45s" fill="freeze"/>')
    parts.append('<text x="34" y="505" class="emph" font-size="31" font-weight="600">Mouad Hassari</text>')
    parts.append('<text x="34" y="531" class="blue" font-size="13">IT-Specialist | Senior Computer Science Student @AUI</text>')
    parts.append(f'<text x="34" y="594" class="emph" font-size="47" font-weight="500">{summary["total"]}</text>')
    parts.append('<text x="34" y="615" class="dim" font-size="11">contributions in the last year</text>')
    parts.append(f'<text x="566" y="570" text-anchor="end" class="emph" font-size="19" font-weight="600">{summary["active"]}</text>')
    parts.append('<text x="566" y="589" text-anchor="end" class="dim" font-size="10">active days</text>')
    parts.append(f'<text x="566" y="623" text-anchor="end" class="emph" font-size="19" font-weight="600">{summary["best_week"]}</text>')
    parts.append('<text x="566" y="642" text-anchor="end" class="dim" font-size="10">best week</text>')
    parts.append(sparkline(summary["weekly"], 34, 646, 532, 56))
    parts.append('</g></svg>')
    return "".join(parts)


def heat_level(value: int, peak: int) -> int:
    if value <= 0:
        return 0
    ratio = value / max(peak, 1)
    if ratio <= 0.25:
        return 1
    if ratio <= 0.5:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


def render_stats_panel(summary: dict) -> str:
    height = 242
    parts = [svg_open(height)]
    parts.append('<line x1="155" y1="18" x2="155" y2="125" class="rule" opacity=".8"/>')
    parts.append('<line x1="310" y1="18" x2="310" y2="125" class="rule" opacity=".8"/>')
    parts.append('<line x1="467" y1="18" x2="467" y2="125" class="rule" opacity=".8"/>')

    current = summary["current"]
    longest = summary["longest"]
    parts.append(f'<text x="34" y="57" class="emph" font-size="31" font-weight="600">{current["length"]}</text>')
    parts.append('<text x="34" y="79" class="dim" font-size="10">current streak</text>')
    parts.append(f'<text x="34" y="99" class="blue" font-size="9">{escape(fmt_range(current))}</text>')

    parts.append(f'<text x="185" y="57" class="emph" font-size="31" font-weight="600">{longest["length"]}</text>')
    parts.append('<text x="185" y="79" class="dim" font-size="10">longest streak</text>')
    parts.append(f'<text x="185" y="99" class="blue" font-size="9">{escape(fmt_range(longest))}</text>')

    parts.append('<text x="331" y="31" class="dim" font-size="9" letter-spacing="1">TOP LANGUAGES</text>')
    for index, (name, percentage) in enumerate(summary["languages"][:5]):
        y = 53 + index * 15
        parts.append(f'<text x="331" y="{y}" class="emph" font-size="9" font-weight="600">{escape(name)}</text>')
        bar_width = max(4, 72 * percentage / 100)
        parts.append(f'<rect x="391" y="{y - 7}" width="72" height="5" rx="2.5" class="soft" opacity=".25"/>')
        parts.append(f'<rect x="391" y="{y - 7}" width="{bar_width:.1f}" height="5" rx="2.5" class="ink"/>')
        parts.append(f'<text x="463" y="{y}" text-anchor="end" class="dim" font-size="8">{percentage:.0f}%</text>')

    parts.append('<text x="485" y="31" class="dim" font-size="9" letter-spacing="1">LAST 90 DAYS</text>')
    end = summary["as_of"]
    start = end - timedelta(days=89)
    # Align the first column to Sunday for a GitHub-like matrix.
    aligned_start = start - timedelta(days=(start.weekday() + 1) % 7)
    days = [(aligned_start + timedelta(days=index)) for index in range(98)]
    peak = max((summary["counts"].get(day.isoformat(), 0) for day in days), default=1)
    cell = 6
    gap = 2
    base_x = 485
    base_y = 45
    for day in days:
        week = (day - aligned_start).days // 7
        weekday = (day.weekday() + 1) % 7
        value = summary["counts"].get(day.isoformat(), 0)
        level = heat_level(value, peak)
        opacity = "1" if start <= day <= end else ".28"
        parts.append(
            f'<rect x="{base_x + week * (cell + gap)}" y="{base_y + weekday * (cell + gap)}" '
            f'width="{cell}" height="{cell}" rx="1.2" class="cell{level}" opacity="{opacity}"/>'
        )

    parts.append('<line x1="34" y1="144" x2="586" y2="144" class="rule"/>')
    parts.append('<text x="34" y="169" class="dim" font-size="9" letter-spacing="1">PROFILE SIGNAL</text>')
    parts.append('<text x="34" y="194" class="emph" font-size="13" font-weight="600">software · systems · security</text>')
    parts.append('<text x="34" y="216" class="dim" font-size="10">public activity refreshes daily from GitHub GraphQL</text>')
    parts.append('</svg>')
    return "".join(parts)


def write_if_changed(path: Path, content: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="render the included offline demo data")
    args = parser.parse_args()
    summary = load_demo() if args.demo else fetch()
    write_if_changed(ROOT / "hero.svg", render_hero(summary))
    write_if_changed(ROOT / "stats-panel.svg", render_stats_panel(summary))


if __name__ == "__main__":
    main()
