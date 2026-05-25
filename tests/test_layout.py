"""Tests for signforge.layout — pure geometry, no SVG/rendering."""
import pytest

from signforge.glyphs import text_width
from signforge.layout import compute_layout
from signforge.sign import Sign


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _layout(sign, *, main_font, header_font, sub_font):
    return compute_layout(
        sign,
        main_font=main_font,
        header_font=header_font,
        sub_font=sub_font,
    )


# ---------------------------------------------------------------------------
# Auto-fit / clamping
# ---------------------------------------------------------------------------

def test_autofit_shrinks_cap(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """A line wider than the text zone must be shrunk; cap must stay ≤ cap_main_max."""
    # Use a wide sign so letter-spacing (0.04 * n chars) < zone_w.
    # "HELLO WORLD HELLO WORLD HELLO WORLD" is 35 chars → 35*0.04=1.4 in spacing
    # zone_w = 10 - 2 = 8. 1.4 < 8 so the text CAN fit at small enough cap.
    sign = Sign(
        width=10, height=6,
        lines=["HELLO WORLD HELLO WORLD HELLO WORLD"],
        cap_main_max=1.25,
    )
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    zone_w = result.text_zone_x1 - result.text_zone_x0
    for p in result.main:
        w = text_width(p.font, p.text, p.cap_in, p.letter_spacing_in)
        # allow 0.1% tolerance (convergence tolerance in the iterative shrink)
        assert w <= zone_w * 1.001 + 1e-6, f"Line overflows zone: {w:.4f} > {zone_w:.4f}"
    for p in result.main:
        assert p.cap_in <= sign.cap_main_max + 1e-9


def test_cap_main_max_honoured(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """cap_main must never exceed cap_main_max even for a short line."""
    sign = Sign(width=20, height=8, lines=["HI"], cap_main_max=0.8)
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    for p in result.main:
        assert p.cap_in <= 0.8 + 1e-9


def test_header_shrinks_to_fit(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """A very long header must be shrunk to fit the text zone."""
    # ls_header = 0.14 per char.  "VERY LONG HEADER HERE" = 21 chars → 21*0.14=2.94 in.
    # Use width=20 so zone_w=18; 2.94 < 18, so the header can fit at small enough cap.
    sign = Sign(
        width=20, height=6,
        header="VERY LONG HEADER VERY LONG HEADER VERY LONG",
        lines=["X"],
    )
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    zone_w = result.text_zone_x1 - result.text_zone_x0
    assert result.header is not None
    w = text_width(result.header.font, result.header.text,
                   result.header.cap_in, result.header.letter_spacing_in)
    # allow 0.1% tolerance (convergence tolerance in the iterative shrink)
    assert w <= zone_w * 1.001 + 1e-6


# ---------------------------------------------------------------------------
# X-alignment branches
# ---------------------------------------------------------------------------

def test_auto_left_with_emblem(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """text_align='auto' + emblem → left-aligned (x == text_zone_x0)."""
    sign = Sign(
        width=20, height=8,
        style="cyberpunk", emblem="circuit",
        lines=["HELLO WORLD"],
    )
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    for p in result.main:
        assert p.x_in == pytest.approx(result.text_zone_x0)


def test_auto_center_without_emblem(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """text_align='auto' + no emblem → centered in text zone."""
    sign = Sign(width=20, height=8, lines=["HELLO WORLD"])
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    zone_w = result.text_zone_x1 - result.text_zone_x0
    for p in result.main:
        w = text_width(p.font, p.text, p.cap_in, p.letter_spacing_in)
        expected_x = result.text_zone_x0 + (zone_w - w) / 2
        assert p.x_in == pytest.approx(expected_x, abs=1e-6)


def test_explicit_left_overrides_auto(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """text_align='left' must be left-aligned even without an emblem."""
    sign = Sign(width=20, height=8, lines=["HELLO"], text_align="left")
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    for p in result.main:
        assert p.x_in == pytest.approx(result.text_zone_x0)


def test_explicit_center_with_emblem(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """text_align='center' must be centred even with an emblem."""
    sign = Sign(
        width=20, height=8,
        style="cyberpunk", emblem="circuit",
        lines=["HI"], text_align="center",
    )
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    zone_w = result.text_zone_x1 - result.text_zone_x0
    for p in result.main:
        w = text_width(p.font, p.text, p.cap_in, p.letter_spacing_in)
        expected_x = result.text_zone_x0 + (zone_w - w) / 2
        assert p.x_in == pytest.approx(expected_x, abs=1e-6)


# ---------------------------------------------------------------------------
# Vertical centering
# ---------------------------------------------------------------------------

def test_vertical_block_inside_sign(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """The entire text block must fit inside the sign bounds."""
    sign = Sign(
        width=20, height=8,
        header="HDR",
        lines=["LINE ONE", "LINE TWO"],
        sub="// sub //",
    )
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    assert result.header is not None
    assert result.sub is not None
    top = result.header.baseline_y_in - result.header.cap_in
    bottom = result.sub.baseline_y_in
    assert top > 0, "Text block starts above the sign"
    assert bottom < sign.height, "Text block overflows sign height"


def test_vertical_centering_rough(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """Top of block should be within 40% of sign height from the top."""
    sign = Sign(width=20, height=8, header="HDR", lines=["LINE ONE", "LINE TWO"])
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    assert result.header is not None
    top = result.header.baseline_y_in - result.header.cap_in
    assert 0 < top < sign.height * 0.4


# ---------------------------------------------------------------------------
# Emblem zone math
# ---------------------------------------------------------------------------

def test_emblem_zone_positions(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """With an emblem, emblem_cx/cy and text_zone_x0 are correctly derived."""
    sign = Sign(
        width=20, height=8,
        style="cyberpunk", emblem="circuit",
        emblem_zone_width=8.0,
        lines=["X"],
    )
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    assert result.emblem_cx is not None
    assert result.emblem_cy is not None
    # cx lives inside the emblem zone
    assert 0 < result.emblem_cx < sign.emblem_zone_width
    # cy is at sign vertical centre
    assert result.emblem_cy == pytest.approx(sign.height / 2)
    # text zone starts after emblem zone + margin
    assert result.text_zone_x0 == pytest.approx(sign.emblem_zone_width + 0.5)
    assert result.text_zone_x1 == pytest.approx(sign.width - 1.0)


def test_no_emblem_full_width(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """Without an emblem, text zone spans near-full width and emblem fields are None."""
    sign = Sign(width=20, height=8, lines=["X"])
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    assert result.emblem_cx is None
    assert result.emblem_cy is None
    assert result.text_zone_x0 == pytest.approx(1.0)
    assert result.text_zone_x1 == pytest.approx(sign.width - 1.0)


# ---------------------------------------------------------------------------
# Rule (decorative line under header)
# ---------------------------------------------------------------------------

def test_rule_set_with_header(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """rule_y and rule_center_x must be set when a header is present."""
    sign = Sign(width=20, height=8, header="HDR", lines=["X"])
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    assert result.rule_y is not None
    assert result.rule_center_x is not None
    # rule appears after the header baseline
    assert result.header is not None
    assert result.rule_y > result.header.baseline_y_in


def test_rule_none_without_header(space_grotesk_bold, orbitron_bold, space_grotesk_medium):
    """rule_y and rule_center_x must be None when there is no header."""
    sign = Sign(width=20, height=8, lines=["X"])
    result = _layout(sign,
                     main_font=space_grotesk_bold,
                     header_font=orbitron_bold,
                     sub_font=space_grotesk_medium)
    assert result.rule_y is None
    assert result.rule_center_x is None
    assert result.header is None
