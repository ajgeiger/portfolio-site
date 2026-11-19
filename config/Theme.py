"""One place for the colors and fonts used by every chart and component."""


class Theme:
    """A restrained consulting palette: deep navy, one bright accent, quiet grays."""

    NAVY = "#0B1F3A"
    INK = "#1F2A37"
    MUTED = "#6B7280"
    LINE = "#D9DEE7"
    PANEL = "#FFFFFF"
    ACCENT = "#1F5EFF"
    TEAL = "#0E9F8A"
    CORAL = "#E4572E"
    AMBER = "#C98A1B"
    GRAY_SOFT = "#E9ECF1"

    FONT_FAMILY = "Inter, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

    @classmethod
    def figure_layout(cls, height: int = 280) -> dict:
        """Shared Plotly layout settings so every chart looks the same."""
        return {
            "height": height,
            "margin": {"l": 8, "r": 8, "t": 8, "b": 8},
            "paper_bgcolor": cls.PANEL,
            "plot_bgcolor": cls.PANEL,
            "font": {"family": cls.FONT_FAMILY, "color": cls.INK, "size": 12},
            "showlegend": False,
            "hoverlabel": {"bgcolor": cls.NAVY, "font": {"color": "#FFFFFF", "family": cls.FONT_FAMILY}},
        }
