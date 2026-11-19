"""Display names, colors and roles for the natural gas forecast models."""

from config.Theme import Theme


class ForecastModels:
    """One place for how each model is named and drawn."""

    CHAMPION = "chronos"
    CHALLENGER = "gradient_boosting"
    BASELINE = "naive"
    ORDER = ("chronos", "gradient_boosting", "naive", "greykite")

    NAMES = {
        "chronos": "Chronos-2",
        "gradient_boosting": "Gradient boosting",
        "naive": "Naive",
        "greykite": "Greykite",
    }
    ROLES = {
        "chronos": "Champion, in production",
        "gradient_boosting": "Challenger, in staging",
        "naive": "Baseline, repeats the last price",
        "greykite": "Not promoted",
    }
    COLORS = {
        "chronos": Theme.ACCENT,
        "gradient_boosting": Theme.TEAL,
        "naive": Theme.MUTED,
        "greykite": Theme.AMBER,
    }
    STAGE_NAMES = {"production": "Production", "staging": "Staging"}
    STAGE_COLORS = {"production": Theme.ACCENT, "staging": Theme.TEAL}

    BAND_FILL = "rgba(31, 94, 255, 0.12)"
    ACTUAL_COLOR = Theme.NAVY

    @classmethod
    def name(cls, model: str) -> str:
        return cls.NAMES.get(model, model.replace("_", " ").capitalize())

    @classmethod
    def color(cls, model: str) -> str:
        return cls.COLORS.get(model, Theme.MUTED)

    @classmethod
    def ordered(cls, models) -> list[str]:
        """Known models in display order, then any others alphabetically."""
        models = list(dict.fromkeys(models))
        known = [model for model in cls.ORDER if model in models]
        return known + sorted(model for model in models if model not in cls.ORDER)
