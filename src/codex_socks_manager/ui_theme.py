"""One semantic palette for widgets and Rich renderables in the optional UI."""
from textual.theme import Theme

COLORS = {
    "background": "#17191C", "surface": "#202328", "text": "#EEECE6",
    "muted": "#ADB2BA", "border": "#737D8C", "accent": "#9CCBFF",
    "selection": "#303F52", "warning": "#EBC073", "error": "#F29B97",
}


def graphite_theme() -> Theme:
    return Theme(
        name="graphite", primary=COLORS["accent"], secondary=COLORS["muted"],
        accent=COLORS["accent"], foreground=COLORS["text"], background=COLORS["background"],
        surface=COLORS["surface"], panel=COLORS["surface"], success=COLORS["text"],
        warning=COLORS["warning"], error=COLORS["error"],
        variables={f"g-{name}": value for name, value in COLORS.items()},
    )
