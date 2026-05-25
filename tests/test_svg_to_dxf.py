"""Tests for signforge.svg_to_dxf — SVG → DXF round-trip."""
import pytest
import ezdxf

from signforge import Sign, render
from signforge.render import DXF_LAYER_COLORS
from signforge.svg_to_dxf import svg_to_dxf


# ---------------------------------------------------------------------------
# Shared fixture: render the reference cyberpunk sign once per module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cyberpunk_dxf(tmp_path_factory):
    out = tmp_path_factory.mktemp("dxf")
    sign = Sign(
        width=28, height=10, style="cyberpunk", emblem="circuit",
        header="SELF-EFFICACY",
        lines=["EVERY FIX MAKES YOU", "HARDER TO BREAK."],
        sub="// BUILT BY EXPERIENCE //",
    )
    svg_path = out / "sign.svg"
    dxf_path = out / "sign.dxf"
    render(sign, svg_path, dxf_path=dxf_path)
    return ezdxf.readfile(str(dxf_path))


# ---------------------------------------------------------------------------
# Layer presence
# ---------------------------------------------------------------------------

def test_all_dxf_layers_exist(cyberpunk_dxf):
    for layer_name in DXF_LAYER_COLORS:
        assert layer_name in cyberpunk_dxf.layers, f"Missing layer: {layer_name}"


# ---------------------------------------------------------------------------
# Layer colours
# ---------------------------------------------------------------------------

def test_layer_colors_match(cyberpunk_dxf):
    for layer_name, expected_color in DXF_LAYER_COLORS.items():
        layer = cyberpunk_dxf.layers.get(layer_name)
        assert layer is not None, f"Layer not found: {layer_name}"
        assert layer.color == expected_color, (
            f"{layer_name}: expected color {expected_color}, got {layer.color}"
        )


# ---------------------------------------------------------------------------
# Entity counts
# ---------------------------------------------------------------------------

def test_active_layers_have_entities(cyberpunk_dxf):
    """Every layer that the cyberpunk emblem uses must have at least one entity."""
    msp = cyberpunk_dxf.modelspace()
    counts: dict[str, int] = {}
    for entity in msp:
        counts[entity.dxf.layer] = counts.get(entity.dxf.layer, 0) + 1

    active = {"OUTER_CUT", "BORDER", "TEXT", "EMBLEM", "TRACES", "ORNAMENT"}
    for layer_name in active:
        assert counts.get(layer_name, 0) > 0, (
            f"Layer {layer_name} has no entities (counts: {counts})"
        )


# ---------------------------------------------------------------------------
# Y-flip (SVG y-down → DXF y-up)
# ---------------------------------------------------------------------------

def test_entities_have_positive_y(cyberpunk_dxf):
    """After the y-flip, all entity Y coords should be non-negative."""
    msp = cyberpunk_dxf.modelspace()
    for entity in msp:
        if entity.dxftype() == "CIRCLE":
            assert entity.dxf.center.y >= 0, (
                f"Negative Y on CIRCLE: {entity.dxf.center}"
            )
        elif entity.dxftype() == "LINE":
            assert entity.dxf.start.y >= 0
            assert entity.dxf.end.y >= 0


# ---------------------------------------------------------------------------
# Round-trip: manually constructed SVG
# ---------------------------------------------------------------------------

def test_roundtrip_simple_svg(tmp_path):
    """svg_to_dxf on a hand-crafted SVG produces correct layers and entities."""
    svg_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
        'width="10in" height="5in" viewBox="0 0 10 5">\n'
        '  <g id="outer_cut" inkscape:label="OUTER_CUT" '
        'stroke="red" stroke-width="0.01" fill="none">\n'
        '    <rect x="0" y="0" width="10" height="5"/>\n'
        '  </g>\n'
        '  <g id="text_layer" inkscape:label="TEXT" '
        'fill="black" stroke="none" fill-rule="evenodd">\n'
        '    <rect x="1" y="1" width="2" height="1"/>\n'
        '  </g>\n'
        '  <g id="circ_layer" inkscape:label="EMBLEM" '
        'fill="black" stroke="none">\n'
        '    <circle cx="5" cy="2.5" r="0.5"/>\n'
        '  </g>\n'
        '</svg>\n'
    )
    svg_path = tmp_path / "simple.svg"
    dxf_path = tmp_path / "simple.dxf"
    svg_path.write_text(svg_content, encoding="utf-8")

    svg_to_dxf(svg_path, dxf_path, layer_colors=DXF_LAYER_COLORS)
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    layers_used = {e.dxf.layer for e in msp}
    assert "OUTER_CUT" in layers_used
    assert "TEXT" in layers_used
    assert "EMBLEM" in layers_used


def test_roundtrip_circle_y_flipped(tmp_path):
    """A circle at SVG (5, 2) in a 5-unit-tall doc should land at DXF y=3."""
    svg_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
        'width="10in" height="5in" viewBox="0 0 10 5">\n'
        '  <g id="g1" inkscape:label="EMBLEM" fill="black">\n'
        '    <circle cx="5" cy="2" r="0.5"/>\n'
        '  </g>\n'
        '</svg>\n'
    )
    svg_path = tmp_path / "circle.svg"
    dxf_path = tmp_path / "circle.dxf"
    svg_path.write_text(svg_content, encoding="utf-8")
    svg_to_dxf(svg_path, dxf_path)
    doc = ezdxf.readfile(str(dxf_path))
    circles = [e for e in doc.modelspace() if e.dxftype() == "CIRCLE"]
    assert len(circles) == 1
    # SVG y=2 in a H=5 doc → DXF y = 5 - 2 = 3
    assert circles[0].dxf.center.y == pytest.approx(3.0)


def test_roundtrip_no_entities_for_unknown_layer(tmp_path):
    """Groups whose inkscape:label is not in layer_colors still get entities,
    just on an auto-created layer with default color."""
    svg_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
        'width="4in" height="4in" viewBox="0 0 4 4">\n'
        '  <g id="g1" inkscape:label="CUSTOM_LAYER" fill="black">\n'
        '    <rect x="0" y="0" width="1" height="1"/>\n'
        '  </g>\n'
        '</svg>\n'
    )
    svg_path = tmp_path / "custom.svg"
    dxf_path = tmp_path / "custom.dxf"
    svg_path.write_text(svg_content, encoding="utf-8")
    svg_to_dxf(svg_path, dxf_path)
    doc = ezdxf.readfile(str(dxf_path))
    layers_used = {e.dxf.layer for e in doc.modelspace()}
    assert "CUSTOM_LAYER" in layers_used


# ---------------------------------------------------------------------------
# Emblem smoke tests
# ---------------------------------------------------------------------------

def test_cyberpunk_circuit_emblem_nonempty():
    from signforge.emblems import cyberpunk_circuit
    from signforge.styles import SvgGroup
    groups = cyberpunk_circuit(5.0, 5.0, 3.3)
    assert len(groups) > 0
    for g in groups:
        assert isinstance(g, SvgGroup)
        assert g.svg_inner.strip() != ""
        assert g.layer in {"EMBLEM", "TRACES"}


def test_woodcut_storm_emblem_nonempty():
    from signforge.emblems import woodcut_storm
    from signforge.styles import SvgGroup
    groups = woodcut_storm(5.0, 5.0, 3.3)
    assert len(groups) > 0
    for g in groups:
        assert isinstance(g, SvgGroup)
        assert g.svg_inner.strip() != ""
        assert g.layer == "EMBLEM"
