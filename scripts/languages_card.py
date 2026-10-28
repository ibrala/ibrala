#!/usr/bin/env python3
"""Generate a sleek, full-width "Most used languages" PNG for a GitHub profile README.

Counts languages from every repo you OWN (public + private, forks skipped),
so it needs a classic token with the `repo` scope in the GH_TOKEN env var.

Usage:
    GH_USER=ibrala GH_TOKEN=ghp_xxx python scripts/languages_card.py
    python scripts/languages_card.py --demo      # sample data, no token needed
"""
import json
import os
import sys
import urllib.request
from collections import Counter
from xml.sax.saxutils import escape

import cairosvg

USER = os.environ.get("GH_USER", "ibrala")
TOKEN = os.environ.get("GH_TOKEN", "")
OUT = os.environ.get("OUT", "assets/languages.png")
TOP = int(os.environ.get("TOP", "7"))  # how many languages to show
EXCLUDE = {s.strip() for s in os.environ.get("EXCLUDE", "").split(",") if s.strip()}

COLORS = {
    "Java": "#b07219", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Python": "#3572A5", "HTML": "#e34c26", "CSS": "#8957e5", "SCSS": "#c6538c",
    "PHP": "#7a86b8", "C": "#8a8a8a", "C++": "#f34b7d", "C#": "#178600",
    "Shell": "#89e051", "Vue": "#41b883", "SQL": "#e38c00", "Kotlin": "#A97BFF",
    "Go": "#00ADD8", "Rust": "#dea584", "Ruby": "#cc342d", "Swift": "#F05138",
    "Dart": "#00B4AB", "Jupyter Notebook": "#DA5B0B", "Lua": "#4f5fd6",
    "Dockerfile": "#384d54", "Makefile": "#427819",
}
FALLBACK = "#8b949e"


def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "languages-card",
    })
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def fetch_languages():
    totals = Counter()
    page = 1
    while True:
        repos = api("https://api.github.com/user/repos"
                    f"?affiliation=owner&visibility=all&per_page=100&page={page}")
        if not repos:
            break
        for repo in repos:
            if repo.get("fork") or repo.get("owner", {}).get("login", "").lower() != USER.lower():
                continue
            for lang, n in api(repo["languages_url"]).items():
                if lang not in EXCLUDE:
                    totals[lang] += n
        page += 1
    return totals


def demo_languages():
    return Counter({"Java": 38000, "JavaScript": 31000, "HTML": 22000, "CSS": 14000,
                    "Python": 9000, "TypeScript": 6000, "PHP": 2500})


def short(name, limit=13):
    return name if len(name) <= limit else name[: limit - 1] + "\u2026"


def render_svg(totals):
    top = totals.most_common(TOP)
    if not top:
        raise SystemExit("No languages found. Check the token scope and username.")
    total = sum(n for _, n in top)
    pcts = [n / total for _, n in top]

    W, H, PAD, GAP = 900, 150, 36, 4
    inner = W - 2 * PAD
    count = len(top)

    # bar segments (min width so tiny languages stay visible)
    avail = inner - GAP * (count - 1)
    raw = [max(6.0, avail * p) for p in pcts]
    scale = avail / sum(raw)
    widths = [w * scale for w in raw]

    font = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, 'DejaVu Sans', sans-serif"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#161b22"/><stop offset="1" stop-color="#0f1319"/>'
        '</linearGradient></defs>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#bg)" stroke="#30363d"/>',
        f'<text x="{PAD}" y="40" font-family="{font}" font-size="12" font-weight="600" '
        'letter-spacing="1.6" fill="#8b949e">MOST USED LANGUAGES</text>',
        f'<text x="{W - PAD}" y="40" text-anchor="end" font-family="{font}" font-size="12" '
        'fill="#6e7681">public + private repos</text>',
    ]

    x = float(PAD)
    for (name, _), w in zip(top, widths):
        color = COLORS.get(name, FALLBACK)
        out.append(f'<rect x="{x:.2f}" y="56" width="{w:.2f}" height="12" rx="6" fill="{color}"/>')
        x += w + GAP

    col_w = inner / count
    for i, ((name, _), p) in enumerate(zip(top, pcts)):
        cx = PAD + i * col_w
        color = COLORS.get(name, FALLBACK)
        out.append(f'<circle cx="{cx + 5:.1f}" cy="98" r="5" fill="{color}"/>')
        out.append(f'<text x="{cx + 17:.1f}" y="103" font-family="{font}" font-size="15" '
                   f'font-weight="600" fill="#e6edf3">{escape(short(name))}</text>')
        out.append(f'<text x="{cx + 17:.1f}" y="124" font-family="{font}" font-size="13" '
                   f'fill="#8b949e">{p * 100:.1f}%</text>')

    out.append("</svg>")
    return "\n".join(out)


def main():
    demo = "--demo" in sys.argv
    if not demo and not TOKEN:
        raise SystemExit("Set GH_TOKEN (classic token with the repo scope), or use --demo.")
    totals = demo_languages() if demo else fetch_languages()
    svg = render_svg(totals)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=OUT, scale=2)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
