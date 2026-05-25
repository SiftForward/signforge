"""Shared fixtures for signforge tests."""
from pathlib import Path
import pytest

# Fonts live at signforge/fonts/ — two levels up from this file (tests/ → signforge/)
FONTS_DIR = Path(__file__).parent.parent / "fonts"


@pytest.fixture(scope="session")
def orbitron_bold() -> str:
    p = FONTS_DIR / "Orbitron-Bold.ttf"
    assert p.exists(), f"Font not found: {p}"
    return str(p)


@pytest.fixture(scope="session")
def space_grotesk_bold() -> str:
    p = FONTS_DIR / "SpaceGrotesk-Bold.ttf"
    assert p.exists(), f"Font not found: {p}"
    return str(p)


@pytest.fixture(scope="session")
def space_grotesk_medium() -> str:
    p = FONTS_DIR / "SpaceGrotesk-Medium.ttf"
    assert p.exists(), f"Font not found: {p}"
    return str(p)
