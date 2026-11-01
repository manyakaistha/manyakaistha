# Profile artwork and interaction notes

Edit `README.md`, then run `python3 generate_assets.py` to rebuild the artwork,
static alternatives, and `STILL.md`. Python's standard library is sufficient.
The palette and project labels live in the generator.

The hero uses a fixed-seed constellation and precomputed parametric ellipse
positions. Each project illustration animates its own mechanism: chart growth,
graph signals, a reading guide, a heatmap, matching paths, or floating lesson
pages. Text stays still and readable. SVG CSS handles animation without scripts,
external fonts, tracking, or third-party image services.

All motion ends within 4.8 seconds of an asset's animation start. There are no
infinite loops or page-level animation timers. SVG images run in the browser's
image context; the profile cannot install visibility or intersection observers.
Every image has a `prefers-reduced-motion` picture source, an internal reduced
motion rule, and a generated still SVG. The still edition is also linked near
the top of the profile.

The three exploration trails and six project notes use native `details` and
`summary`. GitHub owns their focus, keyboard interaction, and disclosure state.
No private project source or planned project is published by this change.

Validation before publication:

- Parsed all 16 SVGs and checked every local image reference.
- Used GitHub's Markdown API to verify preservation of 8 picture elements and
  10 native disclosure panels.
- Inspected orbital transforms at 0 and 1.2 seconds and verified their final state.
- Observed browser animation durations for all six project illustrations;
  the maximum was 4.65 seconds. The header maximum was 4.8 seconds.
- Confirmed the still header exposes no browser animations.
- Opened a trail with a pointer and closed it with Enter at a 390px viewport;
  no horizontal page overflow was present.

System-level reduced-motion emulation was not available in the preview tools;
the media rules and generated still assets were inspected directly.
