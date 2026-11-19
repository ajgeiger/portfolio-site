"""Write the one line headline that sits at the top of the page."""

from analytics.CoverageSummary import CoverageSummary
from config.Formats import Formats


class InsightWriter:
    """Turn the numbers on screen into a short, plain sentence."""

    def write(
        self, summary: CoverageSummary, top_theme: tuple[str, int] | None, rising: tuple[str, float, str] | None
    ) -> list[str]:
        """Return up to three short insight phrases.

        Args:
            summary: Totals for the current filters.
            top_theme: (name, article count) of the largest theme in the first view.
            rising: (name, change in percentage points, window label) of the fastest riser.
        """
        if summary.rows_with_text == 0:
            return ["No articles match these filters."]
        phrases = []
        if top_theme:
            name, count = top_theme
            share = summary.share(count, summary.rows_with_text)
            phrases.append(f"Top theme: {name}, {Formats.count(count)} articles ({Formats.percent(share)} of coverage)")
        if rising:
            name, change, window = rising
            phrases.append(f"Rising fastest: {name}, {Formats.points(change)} ({window.lower()})")
        phrases.append(f"{Formats.percent(summary.unassigned_share)} of articles are one off or vague stories")
        return phrases
