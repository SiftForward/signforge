# SignForge

**Generate CNC-ready signs as SVG + DXF from a simple form or CLI.**

A [SiftForward](https://siftforward.com) tool. Text is outlined to paths — no font dependency at the machine. Geometry is layer-separated for V-carve and pocket toolpaths.

---

## Web interface

```bash
pip install ".[web]"
uvicorn signforge.web:app --reload
# → open http://localhost:8000
```

Fill in the form, click **Generate Sign**, download your SVG and DXF.

## CLI

```bash
pip install .
python -m signforge \
  --style cyberpunk --emblem circuit \
  --header "SELF-EFFICACY" \
  --line "EVERY FIX MAKES YOU" --line "HARDER TO BREAK." \
  --sub "// BUILT BY EXPERIENCE //" \
  --width 28 --height 10 \
  --out out/sign
```

Writes `out/sign.svg`, `out/sign.dxf`, `out/sign.png`.

## Library

```python
from signforge import Sign, render

sign = Sign(
    width=28, height=10,
    style="cyberpunk", emblem="circuit",
    header="SELF-EFFICACY",
    lines=["EVERY FIX MAKES YOU", "HARDER TO BREAK."],
    sub="// BUILT BY EXPERIENCE //",
)
render(sign, "out/sign.svg", "out/sign.dxf", "out/sign.png")
```

## Styles

| Style | Fonts | Emblems |
|---|---|---|
| `cyberpunk` | Orbitron Bold · Space Grotesk | `circuit` — IC chip + PCB traces |
| `woodcut` | Space Grotesk Bold | `storm` — Hokusai spiral storm |
| `classic` | Space Grotesk Bold | *(none)* |

## DXF layers

| Layer | Color | Toolpath |
|---|---|---|
| `OUTER_CUT` | red | Profile cut, outside line, with tabs |
| `BORDER` | blue | V-bit groove ~0.06" deep |
| `TEXT` | white | V-carve closed letter contours |
| `EMBLEM` | green | Pocket toolpath (filled shapes) |
| `TRACES` | cyan | Engrave on-line, V-bit ~0.06" deep |
| `ORNAMENT` | magenta | V-bit decorative groove |

## PNG preview

Requires one of: `cairosvg` (Linux/macOS), `resvg-py` (Windows, included in `[web]` extras), or Inkscape on PATH.

## Deploy (Railway)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

Connect this repo — Railway detects the `Dockerfile` and `railway.toml` automatically.

## Architecture

```
signforge/
├── sign.py        # Declarative Sign dataclass
├── glyphs.py      # Font → SVG path (fontTools)
├── layout.py      # Pure geometry: positions + cap heights
├── emblems.py     # Emblem renderers: circuit, storm
├── styles.py      # Style registry + font resolution
├── render.py      # Orchestrator: layout + style → SVG + DXF + PNG
├── svg_to_dxf.py  # SVG → DXF, layer-aware
├── web.py         # FastAPI web interface
└── __main__.py    # CLI
```

See [`CLAUDE.md`](CLAUDE.md) for architecture notes and CNC gotchas.

---

*Wisconsin-rooted. Practically built. — [SiftForward](https://siftforward.com)*
