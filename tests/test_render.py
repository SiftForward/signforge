"""Tests for signforge.render — SVG assembly and group structure."""
import xml.etree.ElementTree as ET
import pytest

from signforge import Sign, render

SVG_NS = "{http://www.w3.org/2000/svg}"
INK_NS = "{http://www.inkscape.org/namespaces/inkscape}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_svg(path):
    """Parse SVG; raises if not valid XML."""
    tree = ET.parse(str(path))
    return tree.getroot()


def _group_ids(root):
    return {g.attrib["id"] for g in root.findall(SVG_NS + "g")}


def _group_layers(root):
    return {g.attrib.get(INK_NS + "label") for g in root.findall(SVG_NS + "g")}


# ---------------------------------------------------------------------------
# Per-style smoke tests
# ---------------------------------------------------------------------------

def test_render_classic_valid_svg(tmp_path):
    sign = Sign(width=10, height=4, style="classic", lines=["HELLO WORLD"])
    svg = tmp_path / "classic.svg"
    render(sign, svg)
    root = _parse_svg(svg)
    ids = _group_ids(root)
    assert "outer_cut" in ids
    assert "border_groove" in ids
    assert "text" in ids
    assert "emblem" not in ids
    assert "traces" not in ids


def test_render_cyberpunk_has_emblem_and_traces(tmp_path):
    sign = Sign(
        width=12, height=5, style="cyberpunk", emblem="circuit",
        header="TITLE", lines=["BODY TEXT"],
    )
    svg = tmp_path / "cyberpunk.svg"
    render(sign, svg)
    root = _parse_svg(svg)
    ids = _group_ids(root)
    assert "outer_cut" in ids
    assert "border_groove" in ids
    assert "emblem" in ids
    assert "traces" in ids
    assert "text" in ids


def test_render_woodcut_has_emblem_no_traces(tmp_path):
    sign = Sign(
        width=12, height=5, style="woodcut", emblem="storm",
        lines=["THE STORM"],
    )
    svg = tmp_path / "woodcut.svg"
    render(sign, svg)
    root = _parse_svg(svg)
    ids = _group_ids(root)
    assert "outer_cut" in ids
    assert "emblem" in ids
    assert "text" in ids
    assert "traces" not in ids  # woodcut emblem has no stroked traces layer


# ---------------------------------------------------------------------------
# Border flag
# ---------------------------------------------------------------------------

def test_no_border_removes_groove(tmp_path):
    sign = Sign(width=10, height=4, style="classic", lines=["X"], border=False)
    svg = tmp_path / "no_border.svg"
    render(sign, svg)
    assert "border_groove" not in _group_ids(_parse_svg(svg))


def test_border_present_by_default(tmp_path):
    sign = Sign(width=10, height=4, style="classic", lines=["X"])
    svg = tmp_path / "border.svg"
    render(sign, svg)
    assert "border_groove" in _group_ids(_parse_svg(svg))


# ---------------------------------------------------------------------------
# Emblem absent
# ---------------------------------------------------------------------------

def test_no_emblem_no_emblem_groups(tmp_path):
    sign = Sign(width=10, height=4, style="cyberpunk", emblem=None, lines=["X"])
    svg = tmp_path / "no_emblem.svg"
    render(sign, svg)
    ids = _group_ids(_parse_svg(svg))
    assert "emblem" not in ids
    assert "traces" not in ids


# ---------------------------------------------------------------------------
# Ornament (decorative rule under header)
# ---------------------------------------------------------------------------

def test_ornament_present_with_header(tmp_path):
    sign = Sign(width=10, height=4, style="classic", header="HDR", lines=["X"])
    svg = tmp_path / "with_header.svg"
    render(sign, svg)
    assert "ornament" in _group_ids(_parse_svg(svg))


def test_ornament_absent_without_header(tmp_path):
    sign = Sign(width=10, height=4, style="classic", lines=["X"])
    svg = tmp_path / "no_header.svg"
    render(sign, svg)
    assert "ornament" not in _group_ids(_parse_svg(svg))


# ---------------------------------------------------------------------------
# SVG dimensions
# ---------------------------------------------------------------------------

def test_svg_dimensions_match_sign(tmp_path):
    sign = Sign(width=28, height=10, style="classic", lines=["X"])
    svg = tmp_path / "dims.svg"
    render(sign, svg)
    root = _parse_svg(svg)
    assert root.attrib["width"] == "28in"
    assert root.attrib["height"] == "10in"
    vb = root.attrib["viewBox"].split()
    assert float(vb[2]) == pytest.approx(28.0)
    assert float(vb[3]) == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# DXF output
# ---------------------------------------------------------------------------

def test_dxf_written_alongside_svg(tmp_path):
    sign = Sign(width=10, height=4, style="classic", lines=["X"])
    svg = tmp_path / "sign.svg"
    dxf = tmp_path / "sign.dxf"
    render(sign, svg, dxf_path=dxf)
    assert svg.exists()
    assert dxf.exists()
    assert dxf.stat().st_size > 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_invalid_style_raises(tmp_path):
    sign = Sign(style="nonexistent", lines=["X"])
    with pytest.raises(KeyError, match="nonexistent"):
        render(sign, tmp_path / "fail.svg")


def test_invalid_emblem_raises(tmp_path):
    sign = Sign(style="cyberpunk", emblem="nonexistent", lines=["X"])
    with pytest.raises(ValueError, match="no emblem"):
        render(sign, tmp_path / "fail.svg")


# ---------------------------------------------------------------------------
# Inkscape layer labels (used by svg_to_dxf for layer mapping)
# ---------------------------------------------------------------------------

def test_inkscape_labels_match_dxf_layer_names(tmp_path):
    """Each SVG <g> must carry an inkscape:label that matches a DXF layer name."""
    from signforge.render import DXF_LAYER_COLORS
    sign = Sign(
        width=12, height=5, style="cyberpunk", emblem="circuit",
        header="H", lines=["L"], sub="S",
    )
    svg = tmp_path / "labels.svg"
    render(sign, svg)
    root = _parse_svg(svg)
    labels = _group_layers(root)
    labels.discard(None)
    for label in labels:
        assert label in DXF_LAYER_COLORS, (
            f"inkscape:label '{label}' has no DXF layer color entry"
        )
