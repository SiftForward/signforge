"""Style registry.

Each style is a dict with:
    fonts:  {"header": path, "main": path, "sub": path}
    emblems: {emblem_name: callable(cx, cy, extent) -> list[SvgGroup]}

SvgGroup = (group_id, layer_name, svg_inner_string)

The renderer wraps each SvgGroup as <g id=...> ... </g> and routes group_id
to a DXF layer in svg_to_dxf.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from . import emblems

DEFAULT_FONT_DIR = "/usr/share/fonts/truetype/dejavu"

# Project root is two levels up from this file (signforge/signforge/ → signforge/)
_PROJECT_ROOT = Path(__file__).parent.parent

# SpaceGrotesk-Bold is always bundled; use it as the last-resort fallback so
# the package works on Windows and other platforms without system DejaVu.
_BUNDLED_FALLBACK = _PROJECT_ROOT / "fonts" / "SpaceGrotesk-Bold.ttf"


@dataclass
class SvgGroup:
    group_id: str            # SVG id and inkscape:label
    layer: str               # DXF layer name
    svg_inner: str           # raw SVG element string(s)
    fill_rule: str = "nonzero"   # "nonzero" | "evenodd"
    stroke: Optional[str] = None  # if set, group is stroked not filled
    stroke_width: float = 0.05


EmblemFn = Callable[[float, float, float], list[SvgGroup]]


@dataclass
class Style:
    fonts: dict[str, str]
    emblems: dict[str, EmblemFn]


STYLES: dict[str, Style] = {}


def register(name: str, style: Style) -> None:
    STYLES[name] = style


def get(name: str) -> Style:
    if name not in STYLES:
        raise KeyError(f"Unknown style: {name}. Available: {list(STYLES)}")
    return STYLES[name]


# -------- Built-in styles --------

# Resolve fonts with sensible fallbacks. The user can override per-sign.
def _resolve_font(*candidates: str) -> str:
    import os
    for c in candidates:
        if os.path.exists(c):
            return c
        # Also try relative to project root (where fonts/ directory lives),
        # so tests and installed usage work regardless of CWD.
        project_path = _PROJECT_ROOT / c
        if project_path.exists():
            return str(project_path)
    # Bundled fallback — always present in the project; works on any platform.
    if _BUNDLED_FALLBACK.exists():
        return str(_BUNDLED_FALLBACK)
    # Last resort: system DejaVu (Linux / some macOS installs).
    return f"{DEFAULT_FONT_DIR}/DejaVuSans-Bold.ttf"


register("classic", Style(
    fonts={
        "header": _resolve_font(f"{DEFAULT_FONT_DIR}/DejaVuSerif-Bold.ttf"),
        "main":   _resolve_font(f"{DEFAULT_FONT_DIR}/DejaVuSerif-Bold.ttf"),
        "sub":    _resolve_font(f"{DEFAULT_FONT_DIR}/DejaVuSans-Bold.ttf"),
    },
    emblems={},  # classic has no built-in emblems
))


register("cyberpunk", Style(
    fonts={
        # Prefer Orbitron / Space Grotesk if present (project-local fonts/ dir),
        # otherwise fall back to DejaVu Sans Bold.
        "header": _resolve_font("fonts/Orbitron-Bold.ttf",
                                f"{DEFAULT_FONT_DIR}/DejaVuSansMono-Bold.ttf"),
        "main":   _resolve_font("fonts/SpaceGrotesk-Bold.ttf",
                                f"{DEFAULT_FONT_DIR}/DejaVuSans-Bold.ttf"),
        "sub":    _resolve_font("fonts/SpaceGrotesk-Medium.ttf",
                                f"{DEFAULT_FONT_DIR}/DejaVuSans-Bold.ttf"),
    },
    emblems={
        "circuit": emblems.cyberpunk_circuit,
    },
))


register("woodcut", Style(
    fonts={
        "header": _resolve_font(f"{DEFAULT_FONT_DIR}/DejaVuSans-Bold.ttf"),
        "main":   _resolve_font(f"{DEFAULT_FONT_DIR}/DejaVuSerif-Bold.ttf"),
        "sub":    _resolve_font(f"{DEFAULT_FONT_DIR}/DejaVuSans-Bold.ttf"),
    },
    emblems={
        "storm": emblems.woodcut_storm,
    },
))
