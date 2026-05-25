"""Sign — the declarative description of a sign.

Keep this purely declarative. No path generation, no SVG strings, no font I/O.
Rendering happens in render.py; this is just the shape of the input.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Sign:
    # ---- text content ----
    header: Optional[str] = None         # e.g. "SELF-EFFICACY"
    lines: list[str] = field(default_factory=list)  # main quote lines
    sub: Optional[str] = None            # e.g. "// BUILT BY EXPERIENCE //"

    # ---- dimensions (inches) ----
    width: float = 24.0
    height: float = 8.0

    # ---- style ----
    style: str = "classic"  # "classic" | "cyberpunk" | "woodcut" | ...
    emblem: Optional[str] = None  # style-specific emblem name; None = no emblem

    # ---- typography overrides (optional; otherwise style defaults) ----
    header_font: Optional[str] = None
    main_font: Optional[str] = None
    sub_font: Optional[str] = None

    # ---- layout ----
    # If emblem is set, sign uses emblem-and-text layout (emblem left, text right).
    # If emblem is None, text is centered across the full width.
    emblem_zone_width: float = 8.0    # width allocated to emblem zone
    text_align: str = "auto"          # "auto" | "left" | "center"

    # ---- caps (inches) — auto-fit unless overridden ----
    cap_header: Optional[float] = None
    cap_main: Optional[float] = None
    cap_sub: Optional[float] = None
    cap_main_max: float = 1.25        # ceiling for auto-fit

    # ---- decorative ----
    border: bool = True               # outer decorative groove rectangle

    def has_emblem(self) -> bool:
        return self.emblem is not None
