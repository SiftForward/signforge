"""Font glyph → SVG path conversion.

Core primitive used by every style. Outputs path 'd' strings + transform
so the CNC file has no font dependency — letters become outlined geometry.

All units are inches (1 SVG user unit = 1 inch in our output).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


@dataclass
class GlyphPath:
    """A single glyph rendered as an SVG path with a transform.

    The transform places the glyph in inch coordinates with the correct
    scale and a y-flip (font y-up → SVG y-down)."""
    d: str        # path 'd' attribute (raw glyph contours in font em units)
    tx: float     # translate x (inches)
    ty: float     # translate y (inches, baseline)
    scale: float  # scale factor: font em units → inches


@lru_cache(maxsize=8)
def _font(path: str) -> TTFont:
    return TTFont(path)


def _cap_height_em(font: TTFont) -> float:
    """Return cap height in em units. Prefer OS/2 sCapHeight, fall back to 'H' bbox."""
    os2 = font.get("OS/2")
    if os2 is not None and getattr(os2, "sCapHeight", 0):
        return float(os2.sCapHeight)
    cmap = font.getBestCmap()
    if ord("H") in cmap and "glyf" in font:
        glyf = font["glyf"][cmap[ord("H")]]
        if glyf.numberOfContours:
            return float(glyf.yMax)
    return float(font["head"].unitsPerEm) * 0.7


def text_width(font_path: str, text: str, cap_height_in: float,
               letter_spacing_in: float = 0.0) -> float:
    """Compute rendered width of text at a given cap height, in inches."""
    font = _font(font_path)
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphSet()
    units_per_em = font["head"].unitsPerEm
    scale = cap_height_in / _cap_height_em(font)
    spacing_em = letter_spacing_in / scale
    pen_em = 0.0
    for ch in text:
        cp = ord(ch)
        if cp not in cmap:
            pen_em += units_per_em * 0.3 + spacing_em
            continue
        pen_em += glyph_set[cmap[cp]].width + spacing_em
    return pen_em * scale


def render_text(font_path: str, text: str, cap_height_in: float,
                x_in: float, baseline_y_in: float,
                letter_spacing_in: float = 0.0) -> list[GlyphPath]:
    """Render text as a list of GlyphPath. Caller emits these into SVG."""
    font = _font(font_path)
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphSet()
    units_per_em = font["head"].unitsPerEm
    scale = cap_height_in / _cap_height_em(font)
    spacing_em = letter_spacing_in / scale

    out: list[GlyphPath] = []
    pen_em = 0.0
    for ch in text:
        cp = ord(ch)
        if cp not in cmap:
            pen_em += units_per_em * 0.3 + spacing_em
            continue
        glyph = glyph_set[cmap[cp]]
        pen = SVGPathPen(glyph_set)
        glyph.draw(pen)
        d = pen.getCommands()
        if d.strip():
            tx = x_in + pen_em * scale
            ty = baseline_y_in
            out.append(GlyphPath(d=d, tx=tx, ty=ty, scale=scale))
        pen_em += glyph.width + spacing_em
    return out


def glyphs_to_svg(glyphs: list[GlyphPath], indent: str = "    ") -> str:
    """Emit SVG <path> elements for a list of GlyphPath."""
    parts = []
    for g in glyphs:
        # scale x by +scale, y by -scale to flip
        parts.append(
            f'{indent}<path transform="translate({g.tx:.5f},{g.ty:.5f}) '
            f'scale({g.scale:.6f},{-g.scale:.6f})" d="{g.d}"/>'
        )
    return "\n".join(parts) + ("\n" if parts else "")
