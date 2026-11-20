"""Display names, colors and roles for the natural gas forecast models and tournament stages."""

from config.Theme import Theme


class ForecastModels:
    """One place for how each model, family and stage is named and drawn.

    Stages in the predictions table look like "chronos:champion", "baseline:naive"
    or "production". Production is the stitched forecast made of the event winners.
    """

    CHAMPION = "chronos"
    CHALLENGER = "gradient_boosting"
    BASELINE = "naive"
    PRODUCTION = "production"
    ORDER = ("chronos", "gradient_boosting", "naive", "greykite")
    FAMILIES = ("chronos", "gradient_boosting", "greykite")
    CHAMPION_STAGES = ("chronos:champion", "gradient_boosting:champion", "greykite:champion", "baseline:naive")

    NAMES = {
        "chronos": "Chronos-2",
        "gradient_boosting": "Gradient boosting",
        "naive": "Naive",
        "greykite": "Greykite",
    }
    ROLE_NAMES = {"champion": "Champion", "challenger": "Challenger", "baseline": "Baseline", "naive": "Baseline"}
    COLORS = {
        "chronos": Theme.ACCENT,
        "gradient_boosting": Theme.TEAL,
        "naive": Theme.MUTED,
        "greykite": Theme.AMBER,
    }

    BAND_FILL = "rgba(31, 94, 255, 0.12)"
    ACTUAL_COLOR = Theme.NAVY

    @classmethod
    def name(cls, model: str) -> str:
        return cls.NAMES.get(model, model.replace("_", " ").capitalize())

    @classmethod
    def prose_name(cls, model: str) -> str:
        """The name as it reads inside a sentence: "gradient boosting", but "Chronos-2"."""
        return cls.name(model).lower() if model in ("gradient_boosting", "naive") else cls.name(model)

    @classmethod
    def color(cls, model: str) -> str:
        return cls.COLORS.get(model, Theme.MUTED)

    @classmethod
    def ordered(cls, models) -> list[str]:
        """Known models in display order, then any others alphabetically."""
        models = list(dict.fromkeys(models))
        known = [model for model in cls.ORDER if model in models]
        return known + sorted(model for model in models if model not in cls.ORDER)

    @staticmethod
    def stage_parts(stage: str) -> tuple[str, str]:
        """Split "chronos:champion" into ("chronos", "champion"). "baseline:naive" becomes ("naive", "baseline")."""
        if ":" not in stage:
            return stage, ""
        family, role = stage.split(":", 1)
        return (role, family) if family == "baseline" else (family, role)

    @classmethod
    def stage_name(cls, stage: str) -> str:
        """A readable stage label, such as "Chronos-2 champion" or "Naive baseline"."""
        if stage == cls.PRODUCTION:
            return "Production"
        family, role = cls.stage_parts(stage)
        return f"{cls.name(family)} {role}".strip()
