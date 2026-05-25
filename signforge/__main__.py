"""signforge CLI.

Usage:
    python -m signforge --style cyberpunk --emblem circuit \
        --header "SELF-EFFICACY" \
        --line "EVERY FIX MAKES YOU" --line "HARDER TO BREAK." \
        --sub "// BUILT BY EXPERIENCE //" \
        --width 28 --height 10 \
        --out out/sign
"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import Sign, render


def main():
    p = argparse.ArgumentParser(prog="signforge", description="Generate CNC sign files.")
    p.add_argument("--style", default="classic",
                   help="classic | cyberpunk | woodcut")
    p.add_argument("--emblem", default=None,
                   help="style-specific emblem name (e.g. 'circuit' for cyberpunk)")
    p.add_argument("--header", default=None)
    p.add_argument("--line", action="append", default=[],
                   help="main quote line (repeat for multiple lines)")
    p.add_argument("--sub", default=None)
    p.add_argument("--width", type=float, default=24.0, help="inches")
    p.add_argument("--height", type=float, default=8.0, help="inches")
    p.add_argument("--no-border", action="store_true")
    p.add_argument("--cap-main-max", type=float, default=1.25)
    p.add_argument("--emblem-zone", type=float, default=8.0,
                   help="width allocated to emblem in inches")
    p.add_argument("--out", default="sign",
                   help="output base path (no extension); .svg/.dxf/.png appended")
    args = p.parse_args()

    sign = Sign(
        width=args.width,
        height=args.height,
        style=args.style,
        emblem=args.emblem,
        header=args.header,
        lines=args.line,
        sub=args.sub,
        emblem_zone_width=args.emblem_zone,
        border=not args.no_border,
        cap_main_max=args.cap_main_max,
    )

    base = Path(args.out)
    base.parent.mkdir(parents=True, exist_ok=True)
    render(
        sign,
        svg_path=str(base) + ".svg",
        dxf_path=str(base) + ".dxf",
        png_preview=str(base) + ".png",
    )
    print(f"Wrote {base}.svg, {base}.dxf, {base}.png")


if __name__ == "__main__":
    main()
