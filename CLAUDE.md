# signforge — Notes for Claude Code

A CNC sign generator. Produces SVG + DXF files with text outlined as paths
(no font dependency at the machine) and layer-separated geometry for CAM.

## Core principle

**Layout is pure geometry; rendering is pure I/O; styles are pure data.**
Don't mix these — when in doubt, push behavior into a smaller module rather
than expanding an existing one.

## Architecture

```
signforge/
├── sign.py          # Sign dataclass — declarative description, no logic
├── glyphs.py        # Font glyph → SVG path primitive (uses fontTools)
├── layout.py        # compute_layout(sign) → LayoutResult (positions, baselines)
├── emblems.py       # Emblem renderers: (cx, cy, extent) → list[SvgGroup]
├── styles.py        # Style registry: fonts + emblem map per style name
├── render.py        # Orchestrator: layout + style + emblems → SVG + DXF + PNG
├── svg_to_dxf.py    # SVG → DXF converter, layer-aware
└── __main__.py      # CLI
```

Add a new style: register it in `styles.py`. Add a new emblem: write a
function in `emblems.py` and reference it from a Style's `emblems` dict.

## Conventions

- **Units**: inches everywhere. 1 SVG user unit = 1 inch (we set
  `width="N in" height="N in"` on the root). Don't convert to mm anywhere
  until you write a G-code post-processor that needs it.
- **Coordinate system**: SVG (y grows downward). When converting to DXF
  we flip y so it grows upward (CAM convention). Helper math in
  `emblems._polar` already accounts for this.
- **Letters as paths**: every glyph rendered via `glyphs.render_text` becomes
  a `<path>` with `transform="translate(x,y) scale(s,-s)"`. The y-flip is
  part of the scale, not the translate. The CAM software doesn't need the
  font — anyone opening the SVG will see correct text without it installed.
- **Even-odd vs nonzero fill**:
  - Letters use **evenodd** (letters like O, A, B have holes).
  - Emblems use **nonzero** (overlapping shapes union).
  - Get this wrong and pockets carve out the wrong areas.
- **Path samples per curve**: 60 default in `svg_to_dxf.POLY_SAMPLES`.
  Bump for very large files; lower for faster export. Curves under 0.01"
  collapse to a single segment.

## CNC layer conventions (DXF)

| Layer       | Color | Typical toolpath                    |
|-------------|-------|-------------------------------------|
| OUTER_CUT   | red   | profile cut, outside line, with tabs|
| BORDER      | blue  | V-bit groove, ~0.05–0.08" deep      |
| TEXT        | white | V-carve (closed letter contours)    |
| EMBLEM      | green | pocket toolpath (filled shapes)     |
| TRACES      | cyan  | engrave on line, V-bit ~0.06" deep  |
| ORNAMENT    | magenta| V-bit groove                       |

Adding a new layer: update `DXF_LAYER_COLORS` in `render.py` and ensure
the relevant emblem function emits an `SvgGroup` with that layer name.

## Gotchas (hard-won)

1. **Duplicate layout code is a landmine.** The first iteration had two
   places that computed `x1, x2, xs` and the second silently overwrote
   the first. If you find yourself writing position math in two places,
   stop — refactor to one.
2. **Variable fonts need instancing.** Don't ship a variable font as the
   final asset — `fontTools.varLib.instancer.instantiateVariableFont` at
   the weight you want and save the static instance. Otherwise glyph
   metrics may be wrong at runtime.
3. **Matplotlib's DXF preview lies.** It renders text glyphs with their
   inner holes filled (doesn't honor evenodd). Trust the SVG preview
   (cairosvg), not the matplotlib DXF render, for visual verification.
4. **Auto-fit must be clamped.** A narrow geometric font like Space Grotesk
   will auto-grow much larger than a wide serif at the same width budget.
   Always set `cap_main_max` so swapping fonts doesn't blow up the design.
5. **Emblem extent vs. text zone gap.** Spiral arms grow fast — a
   logarithmic spiral at growth=0.42 over 220° goes from r=0.9 to r=4.5.
   Always compute or test actual extent vs. the nominal `extent` parameter.

## Quick test loop

```bash
python -m signforge --style cyberpunk --emblem circuit \
  --header "SELF-EFFICACY" \
  --line "EVERY FIX MAKES YOU" --line "HARDER TO BREAK." \
  --sub "// BUILT BY EXPERIENCE //" \
  --width 28 --height 10 \
  --out out/test
```

Then `xdg-open out/test.png` (or open it on macOS) to eyeball.

## Future work

- G-code post-processor (per machine/bit/material profile). The DXF round
  trip through CAM is the biggest UX wart.
- Material-aware sizing: minimum stroke width per bit diameter, max pocket
  depth per pass.
- Live preview server — watch the source, regenerate on save, browser
  auto-reload.
- More styles: art deco / WPA poster, schematic, minimal geometric.
- Emblem composer: combine multiple emblems (e.g. circuit + hex labels +
  HUD brackets) as separately-toggleable layers.
