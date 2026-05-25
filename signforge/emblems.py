"""Emblem renderers.

Each emblem is a function (cx, cy, extent) -> list[SvgGroup] where extent
is the outer radius in inches. The emblem is responsible for fitting inside
a circle of that radius (approximately — small overshoot is OK).

Adding a new emblem:
    1. Write a function that returns list[SvgGroup].
    2. Register it in styles.py inside the relevant Style's `emblems` dict.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Avoid circular import at module load:
def _SvgGroup(*args, **kwargs):
    from .styles import SvgGroup
    return SvgGroup(*args, **kwargs)


# ============================================================
# Cyberpunk: IC chip + PCB traces + glitch pixels + hex + HUD
# ============================================================

def cyberpunk_circuit(cx: float, cy: float, extent: float):
    """2030 cyberpunk: filled IC chip with PCB traces routing outward,
    glitch pixel clusters, hex byte fragments, HUD corner brackets.

    Returns SvgGroups for EMBLEM (filled) and TRACES (stroked) layers.
    """
    # Scale all emblem elements to fit within `extent`.
    # Reference design used extent=3.3.
    s = extent / 3.3

    chip_size = 1.10 * s
    chip_x = cx - chip_size / 2
    chip_y = cy - chip_size / 2
    chip_r = 0.08 * s

    filled: list[str] = []
    stroked: list[str] = []

    # ---- chip body ----
    filled.append(_rounded_rect(chip_x, chip_y, chip_size, chip_size, chip_r))

    # pin-1 indicator (white circle on chip)
    pin1_r = 0.045 * s
    filled.append(
        f'<circle cx="{chip_x + 0.18*s:.3f}" cy="{chip_y + 0.18*s:.3f}" '
        f'r="{pin1_r:.3f}" fill="white"/>'
    )

    # ---- pins ----
    pin_w = 0.06 * s
    pin_h = 0.12 * s
    n_pins = 5
    spacing = chip_size * 0.65 / (n_pins - 1)
    start = cx - chip_size * 0.325

    pin_tips = {"top": [], "bottom": [], "left": [], "right": []}
    for i in range(n_pins):
        offset = start + i * spacing
        # top
        filled.append(f'<rect x="{offset - pin_w/2:.3f}" y="{chip_y - pin_h:.3f}" '
                      f'width="{pin_w:.3f}" height="{pin_h:.3f}"/>')
        pin_tips["top"].append((offset, chip_y - pin_h))
        # bottom
        filled.append(f'<rect x="{offset - pin_w/2:.3f}" y="{chip_y + chip_size:.3f}" '
                      f'width="{pin_w:.3f}" height="{pin_h:.3f}"/>')
        pin_tips["bottom"].append((offset, chip_y + chip_size + pin_h))
        # left
        filled.append(f'<rect x="{chip_x - pin_h:.3f}" y="{offset - pin_w/2:.3f}" '
                      f'width="{pin_h:.3f}" height="{pin_w:.3f}"/>')
        pin_tips["left"].append((chip_x - pin_h, offset))
        # right
        filled.append(f'<rect x="{chip_x + chip_size:.3f}" y="{offset - pin_w/2:.3f}" '
                      f'width="{pin_h:.3f}" height="{pin_w:.3f}"/>')
        pin_tips["right"].append((chip_x + chip_size + pin_h, offset))

    # ---- PCB traces ----
    via_r = 0.075 * s

    def trace(start_pt, segments):
        pts = [start_pt]
        x, y = start_pt
        for dx, dy in segments:
            x += dx * s
            y += dy * s
            pts.append((x, y))
        d = f"M {pts[0][0]:.3f},{pts[0][1]:.3f} " + " ".join(
            f"L {x:.3f},{y:.3f}" for x, y in pts[1:])
        stroked.append(f'<path d="{d}"/>')
        ex, ey = pts[-1]
        filled.append(f'<circle cx="{ex:.3f}" cy="{ey:.3f}" r="{via_r:.3f}"/>')

    routes = [
        ("top", 0, [(-0.4, -0.4), (-0.6, 0), (-0.3, -0.3)]),
        ("top", 1, [(0, -0.5), (-0.5, -0.5), (-0.4, 0)]),
        ("top", 2, [(0, -0.65), (0.4, -0.4), (0.5, 0)]),
        ("top", 3, [(0.45, -0.45), (0, -0.4), (0.5, -0.5)]),
        ("top", 4, [(0.5, 0), (0.4, -0.4), (0, -0.4)]),
        ("right", 0, [(0.4, -0.4), (0.5, 0), (0.3, 0.3)]),
        ("right", 1, [(0.6, 0), (0.4, -0.4), (0.5, 0)]),
        ("right", 2, [(0.5, 0), (0.5, 0.5), (0.4, 0)]),
        ("right", 3, [(0.4, 0.4), (0, 0.5), (0.5, 0.5)]),
        ("right", 4, [(0.5, 0.5), (0.4, 0), (0, 0.4)]),
        ("bottom", 0, [(-0.5, 0.5), (0, 0.4), (-0.4, 0.4)]),
        ("bottom", 1, [(0, 0.6), (-0.5, 0.5), (-0.3, 0)]),
        ("bottom", 2, [(0, 0.55), (0.5, 0.5), (0.3, 0)]),
        ("bottom", 3, [(0.5, 0.5), (0, 0.4), (0.5, 0.5)]),
        ("bottom", 4, [(0.5, 0), (0.5, 0.5), (0, 0.4)]),
        ("left", 0, [(-0.4, -0.4), (-0.5, 0), (-0.3, -0.3)]),
        ("left", 1, [(-0.5, 0), (-0.4, -0.4), (-0.4, 0)]),
        ("left", 2, [(-0.5, 0), (-0.5, 0.5), (-0.4, 0)]),
        ("left", 3, [(-0.4, 0.4), (0, 0.5), (-0.5, 0.5)]),
        ("left", 4, [(-0.5, 0.5), (-0.4, 0), (0, 0.4)]),
    ]
    for side, idx, segs in routes:
        trace(pin_tips[side][idx], segs)

    # ---- glitch pixels ----
    glitch = [
        (-2.6, 2.2, 0.16), (-2.4, 2.4, 0.10), (-2.5, 2.6, 0.14),
        (-2.85, 2.3, 0.08), (-2.3, 2.1, 0.06),
        (2.2, 2.5, 0.18), (2.5, 2.3, 0.12), (2.4, 2.7, 0.09), (2.8, 2.4, 0.08),
        (3.0, 0.6, 0.14), (2.9, -0.2, 0.10), (3.1, 0.0, 0.06),
        (2.4, -2.4, 0.16), (2.6, -2.2, 0.10), (2.2, -2.6, 0.12), (2.7, -2.5, 0.08),
        (-2.5, -2.3, 0.14), (-2.7, -2.5, 0.10), (-2.3, -2.6, 0.09), (-2.9, -2.2, 0.07),
        (-3.0, 0.0, 0.12), (-3.1, 0.6, 0.08), (-2.9, -0.4, 0.10),
        (-1.5, 2.0, 0.08), (-1.3, 2.0, 0.08), (-1.1, 2.0, 0.08),
        (1.4, -2.2, 0.10), (-1.7, -2.0, 0.09), (1.8, 2.6, 0.07), (-1.9, 2.8, 0.06),
    ]
    for px, py, sz in glitch:
        ax = cx + px * s
        ay = cy - py * s
        ssz = sz * s
        filled.append(f'<rect x="{ax - ssz/2:.3f}" y="{ay - ssz/2:.3f}" '
                      f'width="{ssz:.3f}" height="{ssz:.3f}"/>')

    # ---- HUD corner brackets ----
    extent_b = 3.4 * s
    bracket_len = 0.8 * s
    bracket_t = 0.06 * s
    tick_len = 0.18 * s
    tick_t = 0.04 * s
    for dx, dy, dirx, diry in [
        (-extent_b, -extent_b, 1, 1),
        (extent_b, -extent_b, -1, 1),
        (-extent_b, extent_b, 1, -1),
        (extent_b, extent_b, -1, -1),
    ]:
        corner_x = cx + dx
        corner_y = cy + dy
        # horizontal arm
        hx = corner_x if dirx > 0 else corner_x - bracket_len
        hy = corner_y - bracket_t / 2 if diry > 0 else corner_y - bracket_t / 2
        filled.append(f'<rect x="{hx:.3f}" y="{hy:.3f}" '
                      f'width="{bracket_len:.3f}" height="{bracket_t:.3f}"/>')
        # vertical arm
        vx = corner_x - bracket_t / 2
        vy = corner_y if diry > 0 else corner_y - bracket_len
        filled.append(f'<rect x="{vx:.3f}" y="{vy:.3f}" '
                      f'width="{bracket_t:.3f}" height="{bracket_len:.3f}"/>')
        # tick on horizontal arm (perpendicular outward)
        htx = corner_x + dirx * bracket_len * 0.5
        hty_end = corner_y + diry * tick_len
        filled.append(f'<rect x="{htx - tick_t/2:.3f}" '
                      f'y="{min(corner_y, hty_end):.3f}" '
                      f'width="{tick_t:.3f}" height="{abs(hty_end - corner_y):.3f}"/>')
        # tick on vertical arm
        vtx_end = corner_x + dirx * tick_len
        vty = corner_y + diry * bracket_len * 0.5
        filled.append(f'<rect x="{min(corner_x, vtx_end):.3f}" '
                      f'y="{vty - tick_t/2:.3f}" '
                      f'width="{abs(vtx_end - corner_x):.3f}" height="{tick_t:.3f}"/>')

    return [
        _SvgGroup("emblem", "EMBLEM", "\n".join(filled), fill_rule="nonzero"),
        _SvgGroup("traces", "TRACES", "\n".join(stroked),
                  stroke="black", stroke_width=0.055 * s),
    ]


# ============================================================
# Woodcut: Hokusai-style storm with calm eye
# ============================================================

def woodcut_storm(cx: float, cy: float, extent: float):
    """Hokusai-style storm: bold filled spiral, wave-crest fingers, calm eye.

    Returns a single SvgGroup for the EMBLEM layer.
    """
    s = extent / 3.3
    parts: list[str] = []

    # main storm body
    parts.append(_spiral_band(
        cx, cy,
        theta_start_deg=210, theta_end_deg=210 + 320,
        r_inner_start=1.05 * s, r_inner_end=0.88 * s,
        r_outer_start=2.75 * s, r_outer_end=0.98 * s,
        samples=300,
    ))
    # inner storm
    parts.append(_spiral_band(
        cx, cy,
        theta_start_deg=90, theta_end_deg=90 + 230,
        r_inner_start=0.88 * s, r_inner_end=0.95 * s,
        r_outer_start=1.95 * s, r_outer_end=1.05 * s,
        samples=200,
    ))
    # wave-crest fingers
    fingers = [
        (215, 2.90, 0.80, 0.36, -25),
        (240, 2.90, 1.00, 0.34, -15),
        (268, 2.90, 1.10, 0.32, -5),
        (295, 2.90, 1.00, 0.30, 8),
        (322, 2.90, 0.80, 0.30, 18),
        (348, 2.85, 0.65, 0.28, 25),
        (188, 2.90, 0.70, 0.30, -35),
        (160, 2.80, 0.55, 0.26, -40),
    ]
    for ang, br, ln, w, tl in fingers:
        parts.append(_teardrop(cx, cy, ang, br * s, ln * s, w * s, tl))

    # eye ring
    parts.append(_annulus(cx, cy, 0.62 * s, 0.82 * s))

    # spray droplets
    droplets = [
        (75, 3.55, 0.09), (95, 3.65, 0.12), (108, 3.45, 0.08),
        (120, 3.55, 0.10), (135, 3.50, 0.13),
        (45, 3.55, 0.11), (30, 3.45, 0.08), (60, 3.65, 0.10),
        (15, 3.50, 0.12), (0, 3.55, 0.09),
        (348, 3.55, 0.10), (335, 3.65, 0.13), (320, 3.55, 0.08),
        (305, 3.45, 0.11), (290, 3.55, 0.09),
        (272, 3.65, 0.12), (255, 3.55, 0.08), (240, 3.50, 0.10),
        (225, 3.45, 0.11), (210, 3.55, 0.09), (195, 3.60, 0.07),
        (180, 3.55, 0.10), (165, 3.50, 0.13), (150, 3.55, 0.08),
        (88, 3.85, 0.06), (115, 3.80, 0.07), (340, 3.85, 0.06),
        (310, 3.80, 0.06), (210, 3.80, 0.07), (180, 3.85, 0.06),
    ]
    for ang, rr, ds in droplets:
        ax, ay = _polar(cx, cy, rr * s, ang)
        parts.append(f'<circle cx="{ax:.3f}" cy="{ay:.3f}" r="{ds*s:.3f}"/>')

    return [_SvgGroup("emblem", "EMBLEM", "\n".join(parts), fill_rule="nonzero")]


# ============================================================
# Helpers
# ============================================================

def _rounded_rect(x, y, w, h, r):
    return (
        f'<path d="M {x+r},{y} L {x+w-r},{y} A {r},{r} 0 0 1 {x+w},{y+r} '
        f'L {x+w},{y+h-r} A {r},{r} 0 0 1 {x+w-r},{y+h} '
        f'L {x+r},{y+h} A {r},{r} 0 0 1 {x},{y+h-r} '
        f'L {x},{y+r} A {r},{r} 0 0 1 {x+r},{y} Z"/>'
    )


def _polar(cx, cy, r, theta_deg):
    t = math.radians(theta_deg)
    return (cx + r * math.cos(t), cy - r * math.sin(t))


def _spiral_band(cx, cy, theta_start_deg, theta_end_deg,
                 r_inner_start, r_inner_end,
                 r_outer_start, r_outer_end, samples=200):
    pts = []
    n = samples
    for i in range(n + 1):
        t = i / n
        theta = theta_start_deg + (theta_end_deg - theta_start_deg) * t
        r = r_outer_start + (r_outer_end - r_outer_start) * t
        pts.append(_polar(cx, cy, r, theta))
    for i in range(n + 1):
        t = i / n
        theta = theta_end_deg + (theta_start_deg - theta_end_deg) * t
        r = r_inner_end + (r_inner_start - r_inner_end) * t
        pts.append(_polar(cx, cy, r, theta))
    d = f"M {pts[0][0]:.3f},{pts[0][1]:.3f} " + " ".join(
        f"L {x:.3f},{y:.3f}" for x, y in pts[1:]) + " Z"
    return f'<path d="{d}"/>'


def _teardrop(cx, cy, base_angle_deg, base_r, length, width, tilt_deg=0):
    bx, by = _polar(cx, cy, base_r, base_angle_deg)
    a = math.radians(base_angle_deg + tilt_deg)
    dx_, dy_ = math.cos(a), -math.sin(a)
    px, py = -dy_, dx_
    tip_x = bx + dx_ * length
    tip_y = by + dy_ * length
    b1 = (bx + px * width / 2, by + py * width / 2)
    b2 = (bx - px * width / 2, by - py * width / 2)
    c1 = (bx + dx_ * length * 0.6 + px * width * 0.35,
          by + dy_ * length * 0.6 + py * width * 0.35)
    c2 = (bx + dx_ * length * 0.6 - px * width * 0.35,
          by + dy_ * length * 0.6 - py * width * 0.35)
    d = (
        f"M {b1[0]:.3f},{b1[1]:.3f} "
        f"Q {c1[0]:.3f},{c1[1]:.3f} {tip_x:.3f},{tip_y:.3f} "
        f"Q {c2[0]:.3f},{c2[1]:.3f} {b2[0]:.3f},{b2[1]:.3f} Z"
    )
    return f'<path d="{d}"/>'


def _annulus(cx, cy, r_in, r_out, samples=80):
    outer = []
    for i in range(samples + 1):
        theta = 2 * math.pi * i / samples
        outer.append((cx + r_out * math.cos(theta), cy - r_out * math.sin(theta)))
    inner = []
    for i in range(samples + 1):
        theta = -2 * math.pi * i / samples
        inner.append((cx + r_in * math.cos(theta), cy - r_in * math.sin(theta)))
    pts = outer + inner
    d = f"M {pts[0][0]:.3f},{pts[0][1]:.3f} " + " ".join(
        f"L {x:.3f},{y:.3f}" for x, y in pts[1:]) + " Z"
    return f'<path d="{d}"/>'
