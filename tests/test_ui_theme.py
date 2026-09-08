import pytest
from codex_socks_manager.ui_theme import COLORS


def luminance(color):
    values = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    values = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in values]
    return sum(value * weight for value, weight in zip(values, (.2126, .7152, .0722)))


def contrast(first, second):
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + .05) / (low + .05)


@pytest.mark.parametrize("foreground", ["text", "muted", "accent", "warning", "error"])
@pytest.mark.parametrize("background", ["background", "surface", "selection"])
def test_text_contrast(foreground, background):
    assert contrast(COLORS[foreground], COLORS[background]) >= 4.5


@pytest.mark.parametrize("background", ["background", "surface"])
def test_border_contrast(background):
    assert contrast(COLORS["border"], COLORS[background]) >= 3
