"""Render — orchestrates sign → SVG + DXF.

Entry point: render(sign, svg_path, dxf_path=None, png_preview=None)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .glyphs import glyphs_to_svg, render_text
from .layout import compute_layout
from .sign import Sign
from .styles import SvgGroup
from .styles import get as get_style
from .svg_to_dxf import svg_to_dxf

# Layer→color mapping for DXF (AutoCAD color indices)
DXF_LAYER_COLORS = {
    "OUTER_CUT": 1,   # red
    "BORDER":    5,   # blue
    "TEXT":      7,   # white
    "EMBLEM":    3,   # green
    "TRACES":    4,   # cyan
    "ORNAMENT":  6,   # magenta
}


def render(sign: Sign, svg_path: str | Path,
           dxf_path: Optional[str | Path] = None,
           png_preview: Optional[str | Path] = None) -> None:
    """Render a sign to SVG (+ optional DXF + optional PNG preview)."""
    svg_path = Path(svg_path)
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    # Resolve style + fonts
    style = get_style(sign.style)
    fonts = {**style.fonts}
    if sign.header_font:
        fonts["header"] = sign.header_font
    if sign.main_font:
        fonts["main"] = sign.main_font
    if sign.sub_font:
        fonts["sub"] = sign.sub_font

    # Compute layout
    layout = compute_layout(
        sign,
        header_font=fonts["header"],
        main_font=fonts["main"],
        sub_font=fonts["sub"],
    )

    # Collect SvgGroups
    groups: list[SvgGroup] = []

    # OUTER_CUT
    groups.append(SvgGroup(
        group_id="outer_cut", layer="OUTER_CUT",
        svg_inner=f'<rect x="0" y="0" width="{sign.width}" height="{sign.height}" '
                  f'rx="0.25" ry="0.25"/>',
        stroke="red", stroke_width=0.01,
    ))

    # BORDER (decorative grooves)
    if sign.border:
        bi = 0.4
        bw = sign.width - 2 * bi
        bh = sign.height - 2 * bi
        groups.append(SvgGroup(
            group_id="border_groove", layer="BORDER",
            svg_inner=(
                f'<rect x="{bi}" y="{bi}" width="{bw}" height="{bh}" rx="0.25" ry="0.25"/>\n'
                f'<rect x="{bi+0.12}" y="{bi+0.12}" '
                f'width="{bw-0.24}" height="{bh-0.24}" rx="0.20" ry="0.20"/>'
            ),
            stroke="blue", stroke_width=0.015,
        ))

    # EMBLEM (if any)
    if sign.has_emblem():
        assert sign.emblem is not None  # has_emblem() guarantees this
        emblem_fn = style.emblems.get(sign.emblem)
        if emblem_fn is None:
            raise ValueError(
                f"Style '{sign.style}' has no emblem '{sign.emblem}'. "
                f"Available: {list(style.emblems)}"
            )
        emblem_extent = sign.emblem_zone_width / 2 - 0.3
        # emblem_cx/cy are always set when has_emblem() is True
        assert layout.emblem_cx is not None and layout.emblem_cy is not None
        groups.extend(emblem_fn(layout.emblem_cx, layout.emblem_cy, emblem_extent))

    # TEXT — gather all glyphs into one filled group
    text_inner: list[str] = []
    placements = []
    if layout.header: placements.append(layout.header)
    placements.extend(layout.main)
    if layout.sub:    placements.append(layout.sub)
    for p in placements:
        glyphs = render_text(p.font, p.text, p.cap_in,
                             p.x_in, p.baseline_y_in, p.letter_spacing_in)
        text_inner.append(glyphs_to_svg(glyphs, indent="    "))
    if text_inner:
        groups.append(SvgGroup(
            group_id="text", layer="TEXT",
            svg_inner="".join(text_inner),
            fill_rule="evenodd",  # letters have holes (O, A, B, ...)
        ))

    # ORNAMENT — header rule (if header present)
    if layout.header and layout.rule_y is not None:
        rule_y = layout.rule_y
        cx_r = layout.rule_center_x
        rule_len, rule_gap = 3.5, 0.6
        ind_size = 0.08
        ind_dot_r = 0.05
        ind_spacing = 0.18
        groups.append(SvgGroup(
            group_id="ornament", layer="ORNAMENT",
            svg_inner=(
                f'<line x1="{cx_r - rule_gap/2 - rule_len}" y1="{rule_y}" '
                f'x2="{cx_r - rule_gap/2}" y2="{rule_y}"/>\n'
                f'<line x1="{cx_r + rule_gap/2}" y1="{rule_y}" '
                f'x2="{cx_r + rule_gap/2 + rule_len}" y2="{rule_y}"/>\n'
                f'<rect x="{cx_r - ind_size/2}" y="{rule_y - ind_size/2}" '
                f'width="{ind_size}" height="{ind_size}"/>\n'
                f'<circle cx="{cx_r - ind_spacing}" cy="{rule_y}" r="{ind_dot_r}"/>\n'
                f'<circle cx="{cx_r + ind_spacing}" cy="{rule_y}" r="{ind_dot_r}"/>'
            ),
            stroke="black", stroke_width=0.04,
        ))

    # Emit SVG
    svg = _assemble_svg(sign, groups)
    svg_path.write_text(svg)

    # DXF
    if dxf_path:
        svg_to_dxf(svg_path, dxf_path, layer_colors=DXF_LAYER_COLORS)

    # PNG preview — try multiple backends so this works on all platforms.
    if png_preview:
        _write_png_preview(svg_path, Path(png_preview), output_width=2400)


def _write_png_preview(svg_path: Path, png_path: Path, output_width: int = 2400) -> None:
    """Render SVG to PNG using the best available backend.

    Backend priority (first one that succeeds wins):
      1. cairosvg     — highest quality; needs native cairo DLL (Linux/macOS)
      2. resvg_py     — Rust-based, zero native deps, pre-built wheels for Windows
      3. Inkscape CLI — requires Inkscape to be installed
    Silently skips if none of the backends are available.
    """
    # 1. cairosvg
    try:
        import cairosvg  # type: ignore[import]
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path),
                         output_width=output_width)
        return
    except (ImportError, OSError, Exception):
        pass

    # 2. resvg_py
    try:
        import resvg_py  # type: ignore[import]
        # dpi=96 is required to resolve inch-based SVG dimensions (width="Nin").
        png_bytes = resvg_py.svg_to_bytes(svg_path=str(svg_path),
                                          width=output_width, dpi=96)
        png_path.write_bytes(png_bytes)
        return
    except (ImportError, Exception):
        pass

    # 3. Inkscape CLI
    import shutil, subprocess
    inkscape = shutil.which("inkscape") or next(
        (p for p in [
            r"C:\Program Files\Inkscape\bin\inkscape.exe",
            r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
        ] if __import__("os").path.exists(p)),
        None,
    )
    if inkscape:
        try:
            subprocess.run(
                [inkscape, "--export-type=png",
                 f"--export-width={output_width}",
                 f"--export-filename={png_path}",
                 str(svg_path)],
                check=True, capture_output=True,
            )
            return
        except Exception:
            pass

    # No backend available — preview silently skipped.


def _assemble_svg(sign: Sign, groups: list[SvgGroup]) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
        f'width="{sign.width}in" height="{sign.height}in" '
        f'viewBox="0 0 {sign.width} {sign.height}">\n'
    ]
    for g in groups:
        if g.stroke is not None:
            attrs = (f'stroke="{g.stroke}" stroke-width="{g.stroke_width}" '
                     f'fill="none" stroke-linecap="round" stroke-linejoin="round"')
        else:
            attrs = f'fill="black" stroke="none" fill-rule="{g.fill_rule}"'
        parts.append(
            f'  <g id="{g.group_id}" inkscape:label="{g.layer}" {attrs}>\n'
            f'{g.svg_inner}\n'
            f'  </g>\n'
        )
    parts.append('</svg>\n')
    return "".join(parts)
