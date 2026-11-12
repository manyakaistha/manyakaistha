"""Build the "Long Exposure" profile artwork.

    python3 tools/build.py            # uses data/contributions.json
    python3 tools/build.py --date 2026-11-12

Every mark in the hero sky is a real day from the contribution calendar: one
star per day, trail brightness from that day's contributions, every trail the
same angular length (as in a real exposure). Geometry is seeded so builds are
reproducible; only the date-driven sky rotation and new data change the image.

Each asset is written twice: `*-motion.svg` (CSS animation, no scripts) and
`*-still.svg` (the settled final frame) for prefers-reduced-motion.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from typeset import italic, mono, serif  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / "contributions.json"

# ---------------------------------------------------------------- palette
INK = "#05060a"
NIGHT = "#0a0f1c"
PAPER = "#f1ebde"
MUTED = "#8a92a6"
DIM = "#4d5468"
AMBER = "#ffa64d"
STAR_TEMPS = ["#9dbcff", "#c2d5ff", "#e9edf7", "#fff0d6", "#ffd09a"]
STAR_WEIGHTS = [0.14, 0.22, 0.34, 0.18, 0.12]


# ---------------------------------------------------------------- seeded rng
def mulberry32(seed: int):
    s = seed & 0xFFFFFFFF

    def rnd() -> float:
        nonlocal s
        s = (s + 0x6D2B79F5) & 0xFFFFFFFF
        t = s
        t = ((t ^ (t >> 15)) * (1 | t)) & 0xFFFFFFFF
        t = (t + (((t ^ (t >> 7)) * (61 | t)) & 0xFFFFFFFF) ^ t) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rnd


def pick(rnd, items, weights):
    x, acc = rnd() * sum(weights), 0.0
    for item, w in zip(items, weights):
        acc += w
        if x <= acc:
            return item
    return items[-1]


def f(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


# ---------------------------------------------------------------- motion
def spring_keyframes(name: str, k: float = 5.2, w: float = 14.0, steps: int = 24) -> str:
    """Damped spring baked to keyframes; displacement comes from per-element vars."""
    rows = []
    for i in range(steps + 1):
        t = i / steps
        d = math.exp(-t * k) * math.cos(t * w)
        if i == steps:
            d = 0.0
        rows.append(
            f"{t*100:.1f}%{{transform:translate(calc(var(--dx)*{d:.3f}),calc(var(--dy)*{d:.3f}))"
            f" rotate(calc(var(--r)*{d:.3f}))}}"
        )
    return f"@keyframes {name}{{{''.join(rows)}}}"


REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def svg(w: int, h: int, title: str, body: str, style: str = "") -> str:
    css = f"<style>{style}{REDUCED}</style>" if style else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t"><title id="t">{title}</title>{css}{body}</svg>\n'
    )


def mono_text(s: str, x, y, size=14, fill=MUTED, anchor="start", tracking=1.6, extra="") -> str:
    d = mono().text_path(s, size, x, y, tracking=tracking, anchor=anchor)
    return f'<path d="{d}" fill="{fill}"{extra}/>'


def serif_text(s: str, x, y, size, fill=PAPER, face=None, anchor="start", tracking=0.0, extra="") -> str:
    d = (face or serif()).text_path(s, size, x, y, tracking=tracking, anchor=anchor)
    return f'<path d="{d}" fill="{fill}"{extra}/>'


def arrow(x, y, s=22, color=AMBER) -> str:
    return (f'<path d="M{f(x)} {f(y+s)} L{f(x+s)} {f(y)} M{f(x+s*0.32)} {f(y)} L{f(x+s)} {f(y)} '
            f'L{f(x+s)} {f(y+s*0.68)}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


# ---------------------------------------------------------------- data
def load_days():
    raw = json.loads(DATA.read_text())
    cal = raw["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    return days, cal["totalContributions"]


def nice_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.day:02d} {d.strftime('%b').upper()} {d.year}"


# ================================================================ HERO
def hero(days, total, today: dt.date, motion: bool) -> str:
    W, H = 1200, 640
    PX, PY = 930, 168                      # celestial pole
    TRAIL = math.radians(34)               # same exposure for every star
    rnd = mulberry32(20250114)             # account birthday: stable sky
    # Sidereal drift: the sky sits ~0.9856 deg further round each night.
    phase = math.radians((today - dt.date(2025, 1, 14)).days * 0.9856)

    n = len(days)
    peak = max(c for _, c in days) or 1
    faint, bright, glow = [], [], []
    marks = {}
    busiest = max(range(n), key=lambda i: (days[i][1], i))
    for i, (date, count) in enumerate(days):
        age = n - 1 - i
        r = 58 + 900 * math.sqrt(age / max(1, n - 1)) + (rnd() - 0.5) * 14
        a0 = rnd() * math.tau + phase
        color = pick(rnd, STAR_TEMPS, STAR_WEIGHTS)
        rnd()  # reserved draw keeps sequence stable if styling changes
        a1 = a0 - TRAIL                      # counter-clockwise on screen
        x0, y0 = PX + r * math.cos(a0), PY + r * math.sin(a0)
        x1, y1 = PX + r * math.cos(a1), PY + r * math.sin(a1)
        d = f"M{f(x0)} {f(y0)}A{f(r)} {f(r)} 0 0 0 {f(x1)} {f(y1)}"
        if i in (busiest, n - 1):
            marks[i] = (x1, y1, date, count)
        if count == 0:
            faint.append(f'<path d="{d}" stroke="{color}"/>')
        else:
            t = math.sqrt(count / peak)
            sw = 0.9 + 2.5 * t
            op = 0.42 + 0.58 * t
            bright.append(f'<path d="{d}" stroke="{color}" stroke-width="{f(sw)}" opacity="{op:.2f}"/>')
            if t > 0.38:
                glow.append(f'<path d="{d}" stroke="{color}" stroke-width="{f(sw*3.2)}"/>')

    # ridge silhouette: seeded midpoint displacement
    rr = mulberry32(7)
    pts = [0.0, 0.0]
    amp = 46.0
    for _ in range(7):
        nxt = []
        for a, b in zip(pts, pts[1:]):
            nxt += [a, (a + b) / 2 + (rr() - 0.5) * amp]
        nxt.append(pts[-1])
        pts, amp = nxt, amp * 0.56
    base = 566
    ridge = " ".join(f"L{f(i * W / (len(pts) - 1))} {f(base + v - 10 * math.sin(i / len(pts) * 3.1))}"
                     for i, v in enumerate(pts))
    ridge_d = f"M0 {H} {ridge.replace('L', 'L', 1)} L{W} {H}Z"

    # ---------------------------------------------------- name, glyph by glyph
    name_parts = []
    gr = mulberry32(42)

    def word(text, face, size, x, y, delay0):
        out = []
        glyphs, _ = face.layout(text, size)
        for k, (_, g, gx, adv) in enumerate(glyphs):
            d = face.glyph_path(g, size, x + gx, y)
            if not motion:
                out.append(d)
                continue
            dx, dy = (gr() - 0.5) * 46, (gr() - 0.5) * 34
            rot = (gr() - 0.5) * 14
            out.append(
                f'<path class="g" style="--dx:{dx:.1f}px;--dy:{dy:.1f}px;--r:{rot:.1f}deg;'
                f'animation-delay:{delay0 + k*0.07:.2f}s" d="{d}"/>'
            )
        if not motion:
            return f'<path d="{"".join(out)}"/>'
        return "".join(out)

    name_parts.append(word("Manya", serif(), 252, 58, 262, 0.35))
    name_parts.append(word("Kaistha", italic(), 252, 176, 448, 0.6))

    # ghost exposures (double image) that converge and vanish
    ghost = ""
    if motion:
        whole = serif().text_path("Manya", 252, 58, 262) + italic().text_path("Kaistha", 252, 176, 448)
        ghost = (
            f'<g style="mix-blend-mode:screen"><path class="gh a" d="{whole}" fill="#5aa2ff"/>'
            f'<path class="gh b" d="{whole}" fill="#ff7a45"/></g>'
        )

    # ---------------------------------------------------- annotations
    ann = []
    for idx, label in ((busiest, "BUSIEST NIGHT"), (n - 1, "TONIGHT")):
        x, y, date, count = marks[idx]
        inside = 0 < x < W and 30 < y < 540
        if not inside:
            continue
        right = x < 1000
        lx = x + (34 if right else -34)
        anchor = "start" if right else "end"
        tx = lx + (6 if right else -6)
        ann.append(
            f'<g class="ann"><circle cx="{f(x)}" cy="{f(y)}" r="9" fill="none" stroke="{AMBER}" stroke-width="1.2"/>'
            f'<path d="M{f(x + (9 if right else -9))} {f(y)}H{f(lx)}" stroke="{AMBER}" stroke-width="1"/>'
            + mono_text(f"{label} · {count}", tx, y - 4, 15, AMBER, anchor, 1.2)
            + mono_text(nice_date(date), tx, y + 17, 14, MUTED, anchor, 1.1)
            + "</g>"
        )

    # pole crosshair
    pole = (f'<g stroke="{MUTED}" stroke-width="1" opacity=".7"><path d="M{PX-12} {PY}h8M{PX+4} {PY}h8'
            f'M{PX} {PY-12}v8M{PX} {PY+4}v8"/></g>'
            + mono_text("NCP", PX + 16, PY - 10, 11, DIM, tracking=1.4))

    active = sum(1 for _, c in days if c)
    first, last = days[0][0], days[-1][0]

    bd, bc = days[busiest]
    exif_l = f"{total:,} CONTRIBUTIONS · {active} ACTIVE NIGHTS · PEAK {nice_date(bd)} ({bc})"
    exif_r = f"{nice_date(first)} → {nice_date(last)}"

    style = ""
    if motion:
        style = (
            spring_keyframes("align")
            + "@keyframes expose{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
            "@keyframes fade{from{opacity:0}to{opacity:1}}"
            "@keyframes ghostA{0%{transform:translate(-14px,7px);opacity:.55}100%{transform:none;opacity:0}}"
            "@keyframes ghostB{0%{transform:translate(12px,-9px);opacity:.45}100%{transform:none;opacity:0}}"
            "@keyframes sat{0%{transform:translate(0,0);opacity:0}4%{opacity:.9}46%{opacity:.9}"
            "50%,100%{transform:translate(1500px,-260px);opacity:0}}"
            "@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}"
            ".sky path{stroke-dasharray:1;animation:expose 6.5s cubic-bezier(.22,.7,.2,1) both}"
            ".g{transform-box:fill-box;transform-origin:50% 60%;animation:align 1.9s linear both}"
            ".gh{animation:1.7s cubic-bezier(.2,.8,.2,1) .25s both}.gh.a{animation-name:ghostA}.gh.b{animation-name:ghostB}"
            ".ann{animation:fade .8s ease-out 5.6s both}"
            ".stamp{animation:fade .5s steps(2) 2.6s both}"
            ".sat{animation:sat 38s linear 7s infinite}.sat circle{animation:blink .9s steps(2) infinite}"
            ".meta{animation:fade 1s ease-out .2s both}"
        )
    path_len = ' pathLength="1"' if motion else ""
    sky_cls = ' class="sky"' if motion else ""

    def group(items, attrs):
        return f'<g{sky_cls} fill="none" stroke-linecap="round" {attrs}>' + "".join(
            p.replace("<path ", f"<path{path_len} ") for p in items) + "</g>"

    body = f"""
<defs>
<radialGradient id="sky" cx="{PX/W:.3f}" cy="{PY/H:.3f}" r="1.1"><stop offset="0" stop-color="#111a33"/><stop offset=".55" stop-color="{NIGHT}"/><stop offset="1" stop-color="{INK}"/></radialGradient>
<linearGradient id="glowH" x1="0" y1="0" x2="0" y2="1"><stop offset=".62" stop-color="#ff8a3d" stop-opacity="0"/><stop offset=".9" stop-color="#ff8a3d" stop-opacity=".16"/></linearGradient>
<radialGradient id="shade" cx=".26" cy=".55" r=".5"><stop offset="0" stop-color="{INK}" stop-opacity=".55"/><stop offset="1" stop-color="{INK}" stop-opacity="0"/></radialGradient>
<filter id="bloom" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="3.2"/></filter>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="22"/></clipPath>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{group(glow, 'opacity=".22" filter="url(#bloom)"')}
{group(faint, 'stroke-width=".7" opacity=".27"')}
{group(bright, '')}
{"" if not motion else '<g class="sat"><circle cx="-60" cy="300" r="1.4" fill="#dfe6ff"/></g>'}
{pole}
<rect width="{W}" height="{H}" fill="url(#shade)"/>
<rect width="{W}" height="{H}" fill="url(#glowH)"/>
{ghost}
<g fill="{PAPER}">{''.join(name_parts)}</g>
{serif_text("AI systems, thoughtful interfaces, open experiments.", 64, 520, 30, "#c9c3b6", italic())}
{''.join(ann)}
<path d="{ridge_d}" fill="#020306"/>
<g class="meta">
{mono_text("PLATE 00 — A YEAR ON GITHUB", 40, 50, 16, MUTED)}
{mono_text("ONE STAR PER DAY · BRIGHTER = BUSIER", W-40, 50, 16, MUTED, "end", 1.2)}
{mono_text(exif_l, 40, H-28, 15, MUTED, tracking=1.1)}
{mono_text(exif_r, W-40, H-28, 15, MUTED, "end", 1.1)}
</g>
<g class="stamp">{mono_text("● ALIGNED", W-40, 80, 16, AMBER, "end")}</g>
</g>"""
    title = (f"Manya Kaistha — AI systems, thoughtful interfaces, open experiments. A long-exposure night sky "
             f"where each of {n} star trails is one day of GitHub activity ({total} contributions).")
    return svg(W, H, title, body, style)


# ================================================================ PLATES
PLATE_W, PLATE_H = 800, 560


def plate_frame(num: str, kicker: str, title: str, stack: str, mech: str, style: str, alt: str,
                motion: bool, seed: int) -> str:
    W, H = PLATE_W, PLATE_H
    rnd = mulberry32(seed)
    dust = "".join(
        f'<circle cx="{f(rnd()*W)}" cy="{f(rnd()*330+20)}" r="{f(0.5+rnd()*0.9)}" opacity="{0.15+rnd()*0.35:.2f}"/>'
        for _ in range(46))
    body = f"""
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NIGHT}"/><stop offset="1" stop-color="{INK}"/></linearGradient></defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g fill="#cfd8ff">{dust}</g>
{mech}
<path d="M40 392H{W-40}" stroke="#fff" stroke-opacity=".1"/>
{mono_text(num, 40, 56, 19, AMBER, tracking=2)}
{mono_text(kicker, W-40, 56, 16, MUTED, "end", 1.2)}
{serif_text(title, 38, 468, 74)}
{mono_text(stack, 40, 518, 18, MUTED, tracking=1.4)}
{arrow(W-66, 440)}
</g>"""
    return svg(W, H, alt, body, style if motion else "")


def anim(motion: bool, cls: str) -> str:
    return f' class="{cls}"' if motion else ""


def plate_analytics(motion):
    lines = [("› which nights were busiest?", PAPER),
             ("SELECT day, count(*) AS commits", "#9dbcff"),
             ("FROM activity GROUP BY day", "#9dbcff"),
             ("ORDER BY commits DESC LIMIT 7;", "#9dbcff")]
    code = "".join(
        f'<g{anim(motion, "ln")} style="animation-delay:{0.2 + i*0.45:.2f}s">'
        + mono_text(t, 40, 130 + i * 40, 18, c, tracking=0) + "</g>"
        for i, (t, c) in enumerate(lines))
    heights = [3, 5, 4, 7, 6, 9, 11]
    cols = []
    for i, hgt in enumerate(heights):
        x = 520 + i * 36
        dots = "".join(
            f'<circle cx="{x}" cy="{f(334 - j*22)}" r="6.5" fill="{AMBER if i == 6 else "#c2d5ff"}" '
            f'opacity="{1 if i == 6 else 0.35 + 0.08*i:.2f}"/>' for j in range(hgt))
        cols.append(f'<g{anim(motion, "col")} style="animation-delay:{2.0 + i*0.12:.2f}s">{dots}</g>')
    style = ("@keyframes type{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}"
             "@keyframes up{from{transform:translateY(40px);opacity:0}to{transform:none;opacity:1}}"
             ".ln{animation:type .5s steps(18) both}.col{animation:up .9s cubic-bezier(.2,1.4,.3,1) both}")
    return plate_frame("01", "QUESTION → SQL", "Analytics Query Engine", "PYTHON · FASTAPI · DUCKDB",
                       code + "".join(cols), style,
                       "01 — Analytics Query Engine. Plain language to inspectable SQL. Python, FastAPI, DuckDB.",
                       motion, 11)


def plate_touchline(motion):
    nodes = [(90, 250), (190, 140), (300, 290), (380, 170), (470, 110), (520, 300), (610, 200), (700, 120), (720, 300)]
    edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (2, 5), (3, 6), (5, 6), (4, 7), (6, 7), (6, 8), (5, 8), (1, 4)]
    path = [0, 2, 3, 6, 7]
    pitch = ('<g fill="none" stroke="#9dbcff" stroke-opacity=".09"><rect x="60" y="86" width="680" height="268" rx="4"/>'
             '<path d="M400 86V354"/><circle cx="400" cy="220" r="52"/><rect x="60" y="160" width="70" height="120"/>'
             '<rect x="670" y="160" width="70" height="120"/></g>')
    e = "".join(f'<path d="M{nodes[a][0]} {nodes[a][1]}L{nodes[b][0]} {nodes[b][1]}"/>' for a, b in edges)
    lit = "".join(
        f'<path{anim(motion, "hop")} pathLength="1" style="animation-delay:{0.6 + k*0.55:.2f}s" '
        f'd="M{nodes[a][0]} {nodes[a][1]}L{nodes[b][0]} {nodes[b][1]}"/>'
        for k, (a, b) in enumerate(zip(path, path[1:])))
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="{7 if i in path else 4.5}" fill="{PAPER if i in path else "#6f7891"}"/>'
        for i, (x, y) in enumerate(nodes))
    rings = "".join(
        f'<circle{anim(motion, "ring")} style="animation-delay:{0.6 + k*0.55:.2f}s" cx="{nodes[i][0]}" cy="{nodes[i][1]}" r="15" '
        f'fill="none" stroke="{AMBER}" stroke-width="1.4"/>' for k, i in enumerate(path))
    labels = (mono_text("QUESTION", 90, 290, 16, MUTED, "middle", 1.2)
              + mono_text("PASSAGE", 380, 150, 16, MUTED, "middle", 1.2)
              + mono_text("SOURCE", 700, 100, 16, AMBER, "middle", 1.2))
    mech = (pitch + f'<g stroke="#8a92a6" stroke-opacity=".35" stroke-width="1.2">{e}</g>'
            f'<g stroke="{AMBER}" stroke-width="2.6" stroke-linecap="round"'
            f'{"" if motion else ""}>{lit}</g>{rings}{dots}{labels}')
    style = ("@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
             "@keyframes ping{0%{opacity:0;transform:scale(.4)}40%{opacity:1}100%{opacity:.9;transform:none}}"
             ".hop{stroke-dasharray:1;animation:draw .55s ease-in-out both}"
             ".ring{transform-box:fill-box;transform-origin:center;animation:ping .7s ease-out both}")
    return plate_frame("02", "EVIDENCE GRAPH", "Touchline", "GRAPHRAG · FASTAPI · LOCAL",
                       mech, style, "02 — Touchline. Follow the evidence. GraphRAG, FastAPI, local retrieval.",
                       motion, 12)


def plate_flux(motion):
    words = ["one", "word", "at", "a", "time,", "your", "pace."]
    cx, base = 400, 270
    face = serif()
    groups = []
    per, cycle = 0.42, len(words) * 0.42 + 1.4
    for i, wd in enumerate(words):
        glyphs, width = face.layout(wd, 156)
        letters = [c for c in wd if c.isalpha()]
        orp_i = max(0, min(len(letters) - 1, (len(letters) - 1) // 2 if len(letters) > 1 else 0))
        gx_orp, adv_orp = glyphs[orp_i][2], glyphs[orp_i][3]
        x0 = cx - (gx_orp + adv_orp / 2)
        parts = []
        for k, (_, g, gx, _) in enumerate(glyphs):
            col = AMBER if k == orp_i else PAPER
            parts.append(f'<path d="{face.glyph_path(g, 156, x0 + gx, base)}" fill="{col}"/>')
        if motion:
            groups.append(f'<g class="w{" last" if i == len(words) - 1 else ""}" style="animation-delay:{i*per:.2f}s">{"".join(parts)}</g>')
        elif wd == "pace.":
            groups.append("".join(parts))
    guides = (f'<path d="M{cx} 120v26M{cx} 296v26" stroke="{AMBER}" stroke-width="2"/>'
              f'<path d="M120 133H680M120 309H680" stroke="#fff" stroke-opacity=".08"/>')
    side = (mono_text("320 WPM", 40, 220, 17, MUTED) + mono_text("PDF · EPUB", 40, 246, 17, DIM))
    a, b = per / cycle * 100, (per / cycle * 100) + 0.01
    style = (f"@keyframes flash{{0%{{opacity:1}}{a:.2f}%{{opacity:1}}{b:.2f}%,100%{{opacity:0}}}}"
             f".w{{opacity:0;animation:flash {cycle:.2f}s steps(1,end) infinite}}"
             f".w.last{{animation-name:last}}"
             f"@keyframes last{{0%{{opacity:1}}{(per+1.4)/cycle*100:.2f}%{{opacity:1}}{(per+1.4)/cycle*100+0.01:.2f}%,100%{{opacity:0}}}}")
    return plate_frame("03", "ONE WORD AT A TIME", "Flux Reader", "TYPESCRIPT · REACT NATIVE · EXPO",
                       guides + side + "".join(groups), style,
                       "03 — Flux Reader. One word, your pace. TypeScript, React Native, Expo.", motion, 13)


def plate_faceinsight(motion):
    cols, rows, cell, x0, y0 = 22, 13, 20, 140, 84
    rnd = mulberry32(5)
    # eyes, mouth: where the model "looks"
    blobs = [(0.42, 0.40, 0.055, 1.0), (0.58, 0.40, 0.055, 0.9), (0.5, 0.72, 0.07, 0.75)]
    cells, heat = [], []
    for j in range(rows):
        for i in range(cols):
            u, v = (i + 0.5) / cols, (j + 0.5) / rows
            e = ((u - 0.5) / 0.2) ** 2 + ((v - 0.52) / 0.46) ** 2
            inside = e < 1
            feature = any(((u - bx) / 0.04) ** 2 + ((v - by) / 0.05) ** 2 < 1 for bx, by, _, _ in blobs[:2]) or \
                (abs(v - 0.72) < 0.03 and abs(u - 0.5) < 0.06)
            base = (0.12 if feature else 0.5 - 0.18 * e) if inside else 0.06 + rnd() * 0.04
            x, y = x0 + i * cell, y0 + j * cell
            cells.append(f'<rect x="{x}" y="{y}" width="{cell-3}" height="{cell-3}" rx="3" opacity="{base:.2f}"/>')
            hval = sum(w * math.exp(-(((u - bx) / s) ** 2 + ((v - by) / (s * 1.6)) ** 2)) for bx, by, s, w in blobs)
            if hval > 0.22 and inside:
                c = AMBER if hval > 0.62 else "#ff7a45" if hval > 0.4 else "#a8466f"
                heat.append(f'<rect x="{x}" y="{y}" width="{cell-3}" height="{cell-3}" rx="3" fill="{c}" '
                            f'opacity="{min(0.95, 0.35 + hval):.2f}"/>')
    scan = (f'<rect{anim(motion, "scan")} x="{x0-6}" y="{y0-6}" width="4" height="{rows*cell+9}" fill="{PAPER}" opacity=".8"/>')
    label = (f'<g{anim(motion, "lbl")}>' + mono_text("PRED 0.94", 760, 150, 17, AMBER, "end", 1.2)
             + mono_text("GRAD-CAM", 760, 176, 16, MUTED, "end", 1.2) + "</g>")
    mech = (f'<g fill="#c2d5ff">{"".join(cells)}</g><g{anim(motion, "heat")}>{"".join(heat)}</g>{scan}{label}')
    style = ("@keyframes sweep{from{transform:translateX(0)}to{transform:translateX(446px)}}"
             "@keyframes reveal{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}"
             "@keyframes fade{from{opacity:0}to{opacity:1}}"
             ".scan{animation:sweep 2.4s cubic-bezier(.6,0,.3,1) .4s both,fade .3s reverse 2.8s both}"
             ".heat{animation:reveal 2.4s cubic-bezier(.6,0,.3,1) .4s both}.lbl{animation:fade .6s 2.9s both}")
    return plate_frame("04", "PREDICTION → WHY", "FaceInsight", "PYTORCH · LORA · NEXT.JS",
                       mech, style, "04 — FaceInsight. Look inside the model. PyTorch, LoRA, Next.js.", motion, 14)


def plate_matching(motion):
    left = [(150, 128 + i * 42) for i in range(6)]
    right = [(650, 128 + i * 42) for i in range(6)]
    pairs = [(0, 2), (1, 0), (2, 4), (3, 1), (4, 5), (5, 3)]
    decided = {0, 2, 3, 5}
    arcs = []
    for k, (a, b) in enumerate(pairs):
        (x1, y1), (x2, y2) = left[a], right[b]
        mx, my = 400, (y1 + y2) / 2 - 30
        col = AMBER if k in decided else "#8a92a6"
        dash = "" if k in decided else ' stroke-dasharray="4 7"'
        pl = ' pathLength="1"' if k in decided else ""
        arcs.append(f'<path{anim(motion, "arc")}{pl} style="animation-delay:{0.7 + k*0.38:.2f}s" '
                    f'd="M{x1} {y1}Q{mx} {f(my)} {x2} {y2}" stroke="{col}"{dash}/>' if motion else
                    f'<path d="M{x1} {y1}Q{mx} {f(my)} {x2} {y2}" stroke="{col}"{dash}/>')
    dl = "".join(f'<circle{anim(motion, "arr")} style="animation-delay:{i*0.1:.2f}s" cx="{x}" cy="{y}" r="7" fill="{PAPER}"/>'
                 for i, (x, y) in enumerate(left))
    dr = "".join(f'<circle cx="{x}" cy="{y}" r="7" fill="none" stroke="{PAPER}" stroke-width="1.6"/>' for x, y in right)
    labels = (mono_text("ARRIVALS", 150, 104, 16, MUTED, "middle", 1.4) + mono_text("CANDIDATES", 650, 104, 16, MUTED, "middle", 1.4))
    mech = f'<g fill="none" stroke-width="1.8" stroke-linecap="round">{"".join(arcs)}</g>{dl}{dr}{labels}'
    style = ("@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
             "@keyframes pop{from{transform:translateX(-40px);opacity:0}to{transform:none;opacity:1}}"
             ".arc[stroke-dasharray]{animation:fade 1s both}"
             ".arc:not([stroke-dasharray]){stroke-dasharray:1;animation:draw .8s ease-in-out both}"
             "@keyframes fade{from{opacity:0}to{opacity:1}}"
             ".arr{transform-box:fill-box;animation:pop .6s cubic-bezier(.2,1.3,.3,1) both}")
    return plate_frame("05", "DELAYED FEEDBACK", "Sequential Matching", "PYTHON · SIMULATION",
                       mech, style, "05 — Sequential Matching. Decisions under uncertainty. Python, simulation, evaluation.",
                       motion, 15)


def plate_learning(motion):
    layers = [4, 6, 6, 3]
    xs = [170, 330, 490, 650]
    pos = [[(x, 220 + (j - (n - 1) / 2) * 44) for j in range(n)] for x, n in zip(xs, layers)]
    edges = []
    for L in range(len(layers) - 1):
        for a in pos[L]:
            for b in pos[L + 1]:
                edges.append(f'<path d="M{a[0]} {f(a[1])}L{b[0]} {f(b[1])}"/>')
    pulses = []
    for L in range(len(layers) - 1):
        for a in pos[L][:: 2]:
            b = pos[L + 1][(pos[L].index(a) + 1) % len(pos[L + 1])]
            pulses.append(f'<path{anim(motion, "p")} pathLength="1" style="animation-delay:{0.4 + L*0.7:.2f}s" '
                          f'd="M{a[0]} {f(a[1])}L{b[0]} {f(b[1])}"/>')
    nodes = "".join(
        f'<circle{anim(motion, "n")} style="animation-delay:{0.3 + L*0.7:.2f}s" cx="{x}" cy="{f(y)}" r="8" '
        f'fill="{AMBER if L == 3 and j == 1 else PAPER}"/>'
        for L, col in enumerate(pos) for j, (x, y) in enumerate(col))
    labels = (mono_text("CONCEPT", 170, 98, 16, MUTED, "middle", 1.4) + mono_text("EXPERIMENT", 650, 98, 16, AMBER, "middle", 1.4))
    mech = (f'<g stroke="#8a92a6" stroke-opacity=".18">{"".join(edges)}</g>'
            f'<g stroke="{AMBER}" stroke-width="2" stroke-linecap="round">{"".join(pulses)}</g>{nodes}{labels}')
    style = ("@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
             "@keyframes lit{0%{opacity:.25}60%{opacity:1}100%{opacity:1}}"
             ".p{stroke-dasharray:1;animation:draw .7s ease-out both}.n{animation:lit .8s both}")
    return plate_frame("06", "CONCEPT → EXPERIMENT", "DL / GenAI Resources", "PYTORCH · NOTEBOOKS · GUIDES",
                       mech, style, "06 — DL / GenAI Resources. Complex ideas, made explorable. PyTorch, notebooks, interactive guides.",
                       motion, 16)


# ================================================================ PULLSTAR (wide)
def pullstar(motion):
    W, H = 1200, 520
    PX, PY = 900, 250
    rnd = mulberry32(31)
    stars = []
    for _ in range(70):
        r = 20 + 230 * math.sqrt(rnd())
        a = rnd() * math.tau
        stars.append((r, a, pick(rnd, STAR_TEMPS, STAR_WEIGHTS), 0.6 + rnd() * 1.6))
    trail = math.radians(48)
    trails = []
    dots = []
    bare = []
    for r, a, c, s in stars:
        x0, y0 = PX + r * math.cos(a), PY + r * math.sin(a)
        x1, y1 = PX + r * math.cos(a - trail), PY + r * math.sin(a - trail)
        trails.append(f'<path{" pathLength=\"1\"" if motion else ""} d="M{f(x0)} {f(y0)}A{f(r)} {f(r)} 0 0 0 {f(x1)} {f(y1)}" '
                      f'stroke="{c}" stroke-width="{f(s)}"/>')
        dots.append(f'<circle cx="{f(x0)}" cy="{f(y0)}" r="{f(s*0.9)}" fill="{c}"/>')
        bare.append(f'<circle cx="{f(x0)}" cy="{f(y0)}" r="{f(s*1.1)}"/>')
    frames = ""
    if motion:
        offs = [(-26, 14, -3), (19, -17, 2.5), (-11, -24, -1.5), (24, 21, 3.5)]
        frames = "".join(
            f'<g class="fr" fill="{("#5aa2ff", "#ff7a45")[i % 2]}" style="--dx:{dx}px;--dy:{dy}px;--r:{rt}deg;'
            f'animation-delay:{0.7 + 0.12*i:.2f}s">{"".join(bare)}</g>'
            for i, (dx, dy, rt) in enumerate(offs))
    clip = f'<clipPath id="disc"><circle cx="{PX}" cy="{PY}" r="236"/></clipPath>'
    window = (f'<circle cx="{PX}" cy="{PY}" r="236" fill="#070b16" stroke="#fff" stroke-opacity=".08"/>'
              f'<g clip-path="url(#disc)">'
              f'<g{anim(motion, "trails")} fill="none" stroke-linecap="round" opacity=".95">{"".join(trails)}</g>'
              f'<g opacity=".8" style="mix-blend-mode:screen">{frames}</g><g{anim(motion, "lock")}>{"".join(dots)}</g></g>'
              f'<g stroke="{AMBER}" stroke-width="1.2" opacity=".8"><path d="M{PX-14} {PY}h9M{PX+5} {PY}h9M{PX} {PY-14}v9M{PX} {PY+5}v9"/></g>')
    status = (f'<g{anim(motion, "s1")}>' + mono_text("5 FRAMES · WOBBLE ±26 PX", PX, 503, 16, MUTED, "middle") + "</g>"
              + f'<g{anim(motion, "s2")}>' + mono_text("ALIGNED · TRAILS 48°", PX, 503, 16, AMBER, "middle") + "</g>") if motion else \
        mono_text("ALIGNED · TRAILS 48°", PX, 503, 16, AMBER, "middle")
    body = f"""
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="22"/></clipPath>{clip}
<radialGradient id="bg" cx=".75" cy=".48" r=".8"><stop offset="0" stop-color="#101833"/><stop offset="1" stop-color="{INK}"/></radialGradient></defs>
<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="url(#bg)"/>
{window}{status}
{mono_text("FEATURED — PUBLIC RELEASE", 48, 64, 17, AMBER, tracking=2)}
{serif_text("PullStar", 44, 230, 168)}
{serif_text("Align the night.", 48, 300, 46, "#c9c3b6", italic())}
{serif_text("Keep the motion.", 48, 350, 46, "#c9c3b6", italic())}
{mono_text("LOCAL MACOS APP · STAR TRAILS · MCP", 48, 432, 17, MUTED)}
{mono_text("APPLE SILICON · MACOS 14+", 48, 462, 17, DIM)}
</g>"""
    style = (spring_keyframes("wob", k=4.2, w=11)
             + "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
             "@keyframes fade{from{opacity:0}to{opacity:1}}"
             "@keyframes out{0%,80%{opacity:1}100%{opacity:0}}"
             ".fr{transform-box:view-box;transform-origin:900px 250px;animation:wob 2.2s linear both,out 3.2s both}"
             ".lock{animation:fade .5s 2.5s both}"
             ".trails path{stroke-dasharray:1;animation:draw 3.6s cubic-bezier(.3,.6,.2,1) 2.9s both}"
             ".s1{animation:out 2.9s both}.s2{animation:fade .5s steps(2) 2.9s both}")
    return svg(W, H, "PullStar — Align the night. Keep the motion. A local macOS app for aligned night-sky images, "
                     "star trails, and MCP automation.", body, style if motion else "")


# ================================================================ FOOTER
def footer(motion):
    W, H = 1200, 300
    body = f"""
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="22"/></clipPath>
<linearGradient id="m" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient></defs>
<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{INK}"/>
<path{anim(motion, "met")} pathLength="1" d="M1010 40L840 128" stroke="url(#m)" stroke-width="2" stroke-linecap="round"/>
{serif_text("Clear skies,", 44, 148, 104, PAPER, italic())}
{serif_text("let’s build something worth looking up at.", 48, 214, 40, "#c9c3b6")}
{mono_text("MANYAKAISTHA.DEV@GMAIL.COM", 48, 264, 18, AMBER)}
{arrow(W-80, 230, 26)}
</g>"""
    style = ("@keyframes shoot{0%{stroke-dashoffset:1;opacity:0}8%{opacity:1}20%{stroke-dashoffset:-.2;opacity:0}100%{opacity:0}}"
             ".met{stroke-dasharray:.6 1;animation:shoot 9s cubic-bezier(.3,0,.2,1) 1.2s infinite}")
    return svg(W, H, "Clear skies — let's build something worth looking up at. manyakaistha.dev@gmail.com", body,
               style if motion else "")


# ================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="ISO date for sky rotation (default: today UTC)")
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(dt.timezone.utc).date()
    days, total = load_days()
    ASSETS.mkdir(exist_ok=True)
    jobs = {
        "hero": lambda m: hero(days, total, today, m),
        "pullstar": pullstar,
        "analytics": plate_analytics,
        "touchline": plate_touchline,
        "flux": plate_flux,
        "faceinsight": plate_faceinsight,
        "matching": plate_matching,
        "learning": plate_learning,
        "footer": footer,
    }
    for name, fn in jobs.items():
        for motion in (True, False):
            out = ASSETS / f"{name}-{'motion' if motion else 'still'}.svg"
            out.write_text(fn(motion))
    # data for the interactive observatory page
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "sky.json").write_text(json.dumps({"total": total, "days": days}, separators=(",", ":")))
    print(f"built {len(jobs)*2} svgs for {today} · {total} contributions over {len(days)} days")


if __name__ == "__main__":
    main()
