# Long Exposure — profile design notes

The profile is an astrophotographer's plate. The hero is a long exposure of the
last year on GitHub: **one star per day**, every trail the same angular length
(as in a real exposure), brightness and width from that day's contributions.
Nothing in the sky is decoration. The name enters as a shaken double exposure
and springs into alignment, which is what PullStar does to night-sky frames.

## Build

    pip install fonttools
    python3 tools/build.py              # or --date YYYY-MM-DD

`tools/build.py` writes `assets/*-motion.svg` (CSS animation, no scripts) and
`assets/*-still.svg` (settled final frame, used for `prefers-reduced-motion`).
Text is converted to glyph outlines (`tools/typeset.py`, GPOS kerning) because
SVG images on GitHub cannot load web fonts. Fonts: Instrument Serif and
JetBrains Mono, both SIL OFL (licences in `tools/fonts`).

Geometry is seeded (Mulberry32), so builds are reproducible. Only two things
change the hero: new contribution data, and the date, which turns the sky by
one sidereal day (~0.9856°) per night.

`.github/workflows/night-sky.yml` refetches the calendar daily with the
workflow token and commits the new sky when it changed. The workflow token
sees public contributions; the cached `data/contributions.json` is kept if the
fetch fails.

## Motion

- Hero: trails expose over 6.5 s; glyphs settle on a damped spring baked into
  keyframes (`spring_keyframes`); ghost exposures converge and vanish; one
  satellite crosses every 38 s.
- Plates: each animates its own mechanism (SQL typing and result columns, an
  evidence path through a graph, RSVP words with the focal letter, a Grad-CAM
  sweep, delayed matches, a forward pass). Only Flux Reader and the footer
  meteor loop.
- Every SVG has an internal reduced-motion rule and a still twin.

## Observatory (`docs/`)

An interactive canvas page served by GitHub Pages from `/docs`. It renders the
same seeded sky. Hold (or Space) to open the shutter, move to shake the
camera, release to align: the recorded wobble unwinds through a spring and the
trails become clean arcs. Hover or use ← → to visit a day. DPR scaling,
clamped delta time, paused when hidden, and a static exposure under reduced
motion.
