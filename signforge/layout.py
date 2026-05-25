"""Layout — pure geometry computation. No SVG, no rendering, no I/O.

Given a Sign + font paths, produces a LayoutResult with all baselines and
x-positions resolved. Renderer consumes this.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .glyphs import text_width
from .sign import Sign


@dataclass
class TextPlacement:
    text: str
    font: str
    cap_in: float
    letter_spacing_in: float
    x_in: float
    baseline_y_in: float


@dataclass
class LayoutResult:
    width: float
    height: float
    emblem_cx: Optional[float] = None     # None when no emblem
    emblem_cy: Optional[float] = None
    emblem_zone_extent: float = 0.0       # outer radius/extent in inches
    text_zone_x0: float = 0.0
    text_zone_x1: float = 0.0
    header: Optional[TextPlacement] = None
    main: list[TextPlacement] = field(default_factory=list)
    sub: Optional[TextPlacement] = None
    # Decorative rule under header
    rule_y: Optional[float] = None
    rule_center_x: Optional[float] = None


# Default letter-spacing values (inches). Style modules may override.
LS_HEADER_DEFAULT = 0.14
LS_MAIN_DEFAULT = 0.04
LS_SUB_DEFAULT = 0.06


def compute_layout(
    sign: Sign,
    *,
    main_font: str,
    header_font: str,
    sub_font: str,
    ls_header: float = LS_HEADER_DEFAULT,
    ls_main: float = LS_MAIN_DEFAULT,
    ls_sub: float = LS_SUB_DEFAULT,
) -> LayoutResult:
    """Resolve all positions and cap heights for a Sign."""
    W, H = sign.width, sign.height

    # Zone math
    if sign.has_emblem():
        emblem_cx = sign.emblem_zone_width / 2 + 0.3   # small left margin
        emblem_cy = H / 2
        text_zone_x0 = sign.emblem_zone_width + 0.5
    else:
        emblem_cx = None
        emblem_cy = None
        text_zone_x0 = 1.0
    text_zone_x1 = W - 1.0
    text_zone_w = text_zone_x1 - text_zone_x0

    # Decide cap heights, with auto-fit clamped to cap_main_max.
    cap_header = sign.cap_header or 0.75
    cap_main = sign.cap_main or sign.cap_main_max
    cap_sub = sign.cap_sub or 0.42

    # Auto-shrink main.  Letter-spacing is additive-per-char (inches, not em),
    # so one scaling step doesn't converge — iterate to < 0.1% tolerance.
    for _ in range(10):
        widest = max((text_width(main_font, ln, cap_main, ls_main) for ln in sign.lines),
                     default=0.0)
        if widest <= text_zone_w * 1.001 or widest == 0:
            break
        cap_main *= text_zone_w / widest

    # Auto-shrink header & sub with the same iterative approach.
    if sign.header:
        for _ in range(10):
            w_header = text_width(header_font, sign.header, cap_header, ls_header)
            if w_header <= text_zone_w * 1.001:
                break
            cap_header *= text_zone_w / w_header
    else:
        w_header = 0.0

    if sign.sub:
        for _ in range(10):
            w_sub = text_width(sub_font, sign.sub, cap_sub, ls_sub)
            if w_sub <= text_zone_w * 1.001:
                break
            cap_sub *= text_zone_w / w_sub
    else:
        w_sub = 0.0

    # Vertical block: header (+ rule) → main lines → subtitle
    line_gap = max(0.25, cap_main * 0.25)
    header_gap = 0.55 if sign.header else 0.0
    sub_gap = 0.55 if sign.sub else 0.0
    rule_space = 0.45 if sign.header else 0.0

    total = (
        (cap_header + rule_space + header_gap if sign.header else 0.0)
        + cap_main * len(sign.lines)
        + line_gap * max(0, len(sign.lines) - 1)
        + (sub_gap + cap_sub if sign.sub else 0.0)
    )
    start_y = (H - total) / 2 + 0.15  # tiny optical nudge for sub-weighted lower text

    # X-alignment
    if sign.text_align == "auto":
        text_align = "left" if sign.has_emblem() else "center"
    else:
        text_align = sign.text_align

    def x_for(width: float) -> float:
        if text_align == "left":
            return text_zone_x0
        return text_zone_x0 + (text_zone_w - width) / 2

    result = LayoutResult(
        width=W, height=H,
        emblem_cx=emblem_cx, emblem_cy=emblem_cy,
        emblem_zone_extent=sign.emblem_zone_width / 2,
        text_zone_x0=text_zone_x0, text_zone_x1=text_zone_x1,
    )

    y = start_y
    if sign.header:
        baseline = y + cap_header
        result.header = TextPlacement(
            text=sign.header, font=header_font,
            cap_in=cap_header, letter_spacing_in=ls_header,
            x_in=x_for(w_header), baseline_y_in=baseline,
        )
        result.rule_y = baseline + rule_space * 0.6
        result.rule_center_x = x_for(w_header) + w_header / 2
        y = baseline + rule_space + header_gap

    for line in sign.lines:
        wl = text_width(main_font, line, cap_main, ls_main)
        baseline = y + cap_main
        result.main.append(TextPlacement(
            text=line, font=main_font,
            cap_in=cap_main, letter_spacing_in=ls_main,
            x_in=x_for(wl), baseline_y_in=baseline,
        ))
        y = baseline + line_gap

    if sign.sub:
        y = y - line_gap + sub_gap
        baseline = y + cap_sub
        result.sub = TextPlacement(
            text=sign.sub, font=sub_font,
            cap_in=cap_sub, letter_spacing_in=ls_sub,
            x_in=x_for(w_sub), baseline_y_in=baseline,
        )

    return result
