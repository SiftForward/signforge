"""signforge — generate CNC-ready signs (SVG + DXF) from text and style modules.

Public API:
    from signforge import Sign, render
    sign = Sign(width=28, height=10, style="cyberpunk")
    sign.header = "SELF-EFFICACY"
    sign.lines  = ["EVERY FIX MAKES YOU", "HARDER TO BREAK."]
    sign.sub    = "// BUILT BY EXPERIENCE //"
    render(sign, "out/sign.svg", "out/sign.dxf")
"""
from .render import render
from .sign import Sign

__all__ = ["Sign", "render"]
__version__ = "0.1.0"
