"""Tests for signforge.glyphs — font → SVG path conversion."""
import pytest

from signforge.glyphs import (
    GlyphPath,
    _cap_height_em,
    _font,
    glyphs_to_svg,
    render_text,
    text_width,
)


# ---------------------------------------------------------------------------
# text_width
# ---------------------------------------------------------------------------

def test_text_width_positive(space_grotesk_bold):
    assert text_width(space_grotesk_bold, "HELLO", 1.0) > 0


def test_text_width_scales_linearly_with_cap(space_grotesk_bold):
    """Width must scale 1:1 with cap height."""
    w1 = text_width(space_grotesk_bold, "HELLO", 1.0)
    w2 = text_width(space_grotesk_bold, "HELLO", 2.0)
    assert w2 == pytest.approx(w1 * 2, rel=1e-6)


def test_text_width_increases_with_more_chars(space_grotesk_bold):
    w1 = text_width(space_grotesk_bold, "A", 1.0)
    w2 = text_width(space_grotesk_bold, "AB", 1.0)
    assert w2 > w1


def test_letter_spacing_increases_width(space_grotesk_bold):
    w_no_ls = text_width(space_grotesk_bold, "HELLO", 1.0, letter_spacing_in=0.0)
    w_ls = text_width(space_grotesk_bold, "HELLO", 1.0, letter_spacing_in=0.1)
    assert w_ls > w_no_ls


def test_letter_spacing_scales_with_count(space_grotesk_bold):
    """Extra spacing per character: 5 chars with ls=0.1 adds 0.5 in over no-ls."""
    w0 = text_width(space_grotesk_bold, "HELLO", 1.0, letter_spacing_in=0.0)
    w1 = text_width(space_grotesk_bold, "HELLO", 1.0, letter_spacing_in=0.1)
    # 5 chars × 0.1 in per char = 0.5 in extra
    assert w1 - w0 == pytest.approx(5 * 0.1, rel=0.01)


def test_text_width_orbitron(orbitron_bold):
    w = text_width(orbitron_bold, "SELF-EFFICACY", 0.75)
    assert w > 0


# ---------------------------------------------------------------------------
# render_text — basic output
# ---------------------------------------------------------------------------

def test_render_text_nonempty(space_grotesk_bold):
    glyphs = render_text(space_grotesk_bold, "HELLO", 0.5, 0.0, 0.5)
    assert len(glyphs) > 0
    for g in glyphs:
        assert isinstance(g, GlyphPath)
        assert g.d.strip() != ""


def test_render_text_all_printable_ascii(space_grotesk_bold):
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    glyphs = render_text(space_grotesk_bold, text, 0.5, 0.0, 0.5)
    assert len(glyphs) > 0


def test_render_text_orbitron(orbitron_bold):
    glyphs = render_text(orbitron_bold, "SELF-EFFICACY", 0.75, 0.0, 0.75)
    assert len(glyphs) > 0


# ---------------------------------------------------------------------------
# Scale math
# ---------------------------------------------------------------------------

def test_scale_math(space_grotesk_bold):
    """GlyphPath.scale must equal cap_height / cap_height_em(font) exactly."""
    font = _font(space_grotesk_bold)
    cap_em = _cap_height_em(font)
    for cap_in in [0.5, 1.0, 1.25]:
        glyphs = render_text(space_grotesk_bold, "ABC", cap_in, 0.0, cap_in)
        for g in glyphs:
            assert g.scale == pytest.approx(cap_in / cap_em, rel=1e-9)


def test_scale_orbitron(orbitron_bold):
    font = _font(orbitron_bold)
    cap_em = _cap_height_em(font)
    glyphs = render_text(orbitron_bold, "HELLO", 0.8, 0.0, 0.8)
    for g in glyphs:
        assert g.scale == pytest.approx(0.8 / cap_em, rel=1e-9)


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------

def test_first_glyph_starts_at_x(space_grotesk_bold):
    """First glyph's tx must equal x_in (pen starts at zero advance)."""
    x_in = 3.5
    glyphs = render_text(space_grotesk_bold, "HELLO", 0.5, x_in, 0.5)
    assert len(glyphs) > 0
    assert glyphs[0].tx == pytest.approx(x_in)


def test_glyph_tx_monotone(space_grotesk_bold):
    """tx positions must be strictly increasing for left-to-right text."""
    glyphs = render_text(space_grotesk_bold, "ABCDE", 0.5, 0.0, 0.5)
    txs = [g.tx for g in glyphs]
    assert txs == sorted(txs), f"tx values not monotone: {txs}"


def test_baseline_y_preserved(space_grotesk_bold):
    """Every GlyphPath.ty must equal the baseline_y_in passed in."""
    baseline = 2.75
    glyphs = render_text(space_grotesk_bold, "HELLO", 0.5, 0.0, baseline)
    for g in glyphs:
        assert g.ty == pytest.approx(baseline)


# ---------------------------------------------------------------------------
# Missing characters / edge cases
# ---------------------------------------------------------------------------

def test_missing_char_no_crash(space_grotesk_bold):
    """Control characters not in the font should not raise."""
    glyphs = render_text(space_grotesk_bold, "\x01\x02\x03", 0.5, 0.0, 0.5)
    assert isinstance(glyphs, list)  # may be empty — just must not crash


def test_empty_string(space_grotesk_bold):
    glyphs = render_text(space_grotesk_bold, "", 0.5, 0.0, 0.5)
    assert glyphs == []
    assert text_width(space_grotesk_bold, "", 0.5) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# glyphs_to_svg
# ---------------------------------------------------------------------------

def test_glyphs_to_svg_produces_path_elements(space_grotesk_bold):
    glyphs = render_text(space_grotesk_bold, "HI", 0.5, 0.0, 0.5)
    svg_frag = glyphs_to_svg(glyphs)
    assert "<path" in svg_frag
    assert 'transform="translate(' in svg_frag


def test_glyphs_to_svg_empty_input(space_grotesk_bold):
    assert glyphs_to_svg([]) == ""
