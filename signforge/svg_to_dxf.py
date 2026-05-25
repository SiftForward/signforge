"""SVG → DXF converter (layer-aware).

Reads the inkscape:label attribute of each group to map to DXF layer name.
Samples curves into polylines at a configurable density.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import ezdxf
from svgpathtools import parse_path

SVG_NS = "{http://www.w3.org/2000/svg}"
INK_NS = "{http://www.inkscape.org/namespaces/inkscape}"

POLY_SAMPLES = 60


def svg_to_dxf(svg_path: str | Path, dxf_path: str | Path,
               layer_colors: dict[str, int] | None = None) -> None:
    svg_path = Path(svg_path)
    dxf_path = Path(dxf_path)
    dxf_path.parent.mkdir(parents=True, exist_ok=True)

    tree = ET.parse(svg_path)
    root = tree.getroot()
    vb = root.attrib["viewBox"].split()
    H = float(vb[3])

    doc = ezdxf.new(dxfversion="R2010", units=ezdxf.units.IN)
    doc.units = ezdxf.units.IN
    msp = doc.modelspace()

    layer_colors = layer_colors or {}
    for name, color in layer_colors.items():
        if name not in doc.layers:
            doc.layers.add(name=name, color=color)

    for g in root.findall(SVG_NS + "g"):
        layer = g.attrib.get(INK_NS + "label") or g.attrib.get("id") or "0"
        if layer not in doc.layers:
            doc.layers.add(name=layer)
        _emit_group(g, msp, layer, H)

    doc.saveas(dxf_path)


def _emit_group(g_elem, msp, layer, H):
    for child in g_elem:
        tag = child.tag.replace(SVG_NS, "")
        if tag == "rect":
            _rect(child, msp, layer, H)
        elif tag == "path":
            _path(child, msp, layer, H)
        elif tag == "circle":
            cx_ = float(child.attrib["cx"])
            cy_ = float(child.attrib["cy"])
            r_ = float(child.attrib["r"])
            msp.add_circle((cx_, H - cy_), r_, dxfattribs={"layer": layer})
        elif tag == "line":
            x1 = float(child.attrib["x1"]); y1 = float(child.attrib["y1"])
            x2 = float(child.attrib["x2"]); y2 = float(child.attrib["y2"])
            msp.add_line((x1, H - y1), (x2, H - y2), dxfattribs={"layer": layer})


def _rect(elem, msp, layer, H):
    x = float(elem.attrib.get("x", 0))
    y = float(elem.attrib.get("y", 0))
    w = float(elem.attrib["width"])
    h = float(elem.attrib["height"])
    rx = float(elem.attrib.get("rx", 0))
    ry = float(elem.attrib.get("ry", rx))
    if rx > 0 or ry > 0:
        d = (
            f"M {x+rx},{y} L {x+w-rx},{y} A {rx},{ry} 0 0 1 {x+w},{y+ry} "
            f"L {x+w},{y+h-ry} A {rx},{ry} 0 0 1 {x+w-rx},{y+h} "
            f"L {x+rx},{y+h} A {rx},{ry} 0 0 1 {x},{y+h-ry} "
            f"L {x},{y+ry} A {rx},{ry} 0 0 1 {x+rx},{y} Z"
        )
        _emit_path_d(d, msp, layer, H, transform=None)
    else:
        pts = [(x, H - y), (x + w, H - y), (x + w, H - (y + h)), (x, H - (y + h))]
        msp.add_lwpolyline(pts, dxfattribs={"layer": layer}, close=True)


def _path(elem, msp, layer, H):
    d = elem.attrib.get("d", "")
    t = elem.attrib.get("transform", "")
    transform = _parse_transform(t) if t else None
    _emit_path_d(d, msp, layer, H, transform=transform)


def _emit_path_d(d, msp, layer, H, transform=None):
    if not d.strip():
        return
    path = parse_path(d)
    for sub in path.continuous_subpaths():
        pts = []
        for i, seg in enumerate(sub):
            steps = 1 if seg.length() < 0.01 else POLY_SAMPLES
            for k in range(steps):
                p = seg.point(k / steps)
                if transform:
                    tx, ty, sx, sy = transform
                    p = complex(p.real * sx + tx, p.imag * sy + ty)
                pts.append((p.real, H - p.imag))
            if i == len(sub) - 1:
                p = seg.point(1.0)
                if transform:
                    tx, ty, sx, sy = transform
                    p = complex(p.real * sx + tx, p.imag * sy + ty)
                pts.append((p.real, H - p.imag))
        # dedupe
        clean = [pts[0]] if pts else []
        for p in pts[1:]:
            if (p[0] - clean[-1][0]) ** 2 + (p[1] - clean[-1][1]) ** 2 > 1e-10:
                clean.append(p)
        if len(clean) >= 2:
            msp.add_lwpolyline(clean, dxfattribs={"layer": layer},
                               close=sub.isclosed())


def _parse_transform(s: str):
    tx = ty = 0.0
    sx = sy = 1.0
    m = re.search(r"translate\(([-\d.eE]+)[,\s]+([-\d.eE]+)\)", s)
    if m:
        tx, ty = float(m.group(1)), float(m.group(2))
    m = re.search(r"scale\(([-\d.eE]+)[,\s]+([-\d.eE]+)\)", s)
    if m:
        sx, sy = float(m.group(1)), float(m.group(2))
    else:
        m = re.search(r"scale\(([-\d.eE]+)\)", s)
        if m:
            sx = sy = float(m.group(1))
    return (tx, ty, sx, sy)
