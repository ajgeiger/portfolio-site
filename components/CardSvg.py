"""Draw the hub circle and the branch cards of the topic graph as small SVG images."""

import html
import textwrap
from urllib.parse import quote

from config.Theme import Theme


class CardSvg:
    """Render graph nodes as SVG data URIs.

    The graph library draws each node as a plain shape, so the text, the
    accent stripe and the share bar are drawn into an SVG image and set as
    the node background. This keeps every card crisp at any zoom level.
    """

    BRANCH_SIZE = (290, 108)
    HEADLINE_SIZE = (340, 116)
    HUB_SIZE = 210
    RADIUS = 10
    ACCENT_X = 8
    ACCENT_WIDTH = 5
    BAR_HEIGHT = 6

    FONT = "Inter, Segoe UI, Helvetica Neue, Arial, sans-serif"

    STRIPES = {
        "group": Theme.ACCENT,
        "topic": Theme.TEAL,
        "unassigned": Theme.MUTED,
        "missing": Theme.CORAL,
        "Representative": Theme.ACCENT,
        "Sampled": Theme.AMBER,
    }

    @staticmethod
    def data_uri(svg: str) -> str:
        return "data:image/svg+xml;utf8," + quote(svg)

    @staticmethod
    def text(
        x: float,
        y: float,
        content: str,
        size: int,
        color: str,
        weight: int = 400,
        anchor: str = "start",
        spacing: float = 0,
    ) -> str:
        return (
            f'<text x="{x}" y="{y}" font-family="{CardSvg.FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}" letter-spacing="{spacing}">{html.escape(content)}</text>'
        )

    @classmethod
    def clip(cls, width: int, height: int) -> str:
        """Keep fills inside the rounded card so accents cannot stick out."""
        return (
            f'<defs><clipPath id="card">'
            f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="{cls.RADIUS}"/>'
            f"</clipPath></defs>"
        )

    @classmethod
    def frame(cls, width: int, height: int, border: str, border_width: int) -> str:
        """The white rounded card body. The stroke is drawn later, on top."""
        return (
            f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="{cls.RADIUS}" '
            f'fill="#FFFFFF"/>'
            f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="{cls.RADIUS}" '
            f'fill="none" stroke="{border}" stroke-width="{border_width}"/>'
        )

    @classmethod
    def accent(cls, height: int, color: str) -> str:
        """An inset vertical pill, clipped to the card, with rounded ends."""
        top = 12
        bar_height = max(height - 24, 8)
        radius = cls.ACCENT_WIDTH / 2
        return (
            f'<g clip-path="url(#card)">'
            f'<rect x="{cls.ACCENT_X}" y="{top}" width="{cls.ACCENT_WIDTH}" height="{bar_height}" '
            f'rx="{radius}" fill="{color}"/>'
            f"</g>"
        )

    @classmethod
    def bar(cls, x: float, y: float, width: float, color: str) -> str:
        """A horizontal share bar with fully rounded ends."""
        radius = cls.BAR_HEIGHT / 2
        return (
            f'<rect x="{x}" y="{y}" width="{width:.1f}" height="{cls.BAR_HEIGHT}" '
            f'rx="{radius}" fill="{color}"/>'
        )

    @staticmethod
    def shorten(content: str, characters: int) -> str:
        return content if len(content) <= characters else content[: characters - 1].rstrip() + "\u2026"

    @classmethod
    def wrap(cls, content: str, characters: int, lines: int) -> list[str]:
        wrapped = textwrap.wrap(content, characters) or [""]
        if len(wrapped) > lines:
            wrapped = wrapped[:lines]
            wrapped[-1] = cls.shorten(wrapped[-1] + " \u2026", characters)
        return wrapped

    @classmethod
    def branch(
        cls, kicker: str, name: str, detail: str, share_of_view: float, style: str, renamed: bool = False
    ) -> str:
        """A branch card: kicker, name, counts and a bar for its share of the current view."""
        width, height = cls.BRANCH_SIZE
        stripe = cls.STRIPES.get(style, Theme.ACCENT)
        bar_width = width - 40
        filled = max(2.0, min(1.0, share_of_view) * bar_width)
        kicker_text = kicker + ("  \u00b7  RENAMED" if renamed else "")
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
            cls.clip(width, height),
            cls.frame(width, height, Theme.LINE, 1),
            cls.accent(height, stripe),
            cls.text(22, 26, kicker_text, 10, Theme.MUTED, 600, spacing=1.2),
            cls.text(22, 50, cls.shorten(name, 27), 16, Theme.NAVY, 700),
            cls.text(22, 72, detail, 12, Theme.INK),
            cls.bar(22, 86, bar_width, Theme.GRAY_SOFT),
            cls.bar(22, 86, filled, stripe),
            "</svg>",
        ]
        return cls.data_uri("".join(parts))

    @classmethod
    def headline(cls, tag: str, title: str, footer: str, selected: bool = False) -> str:
        """A headline card with its tag, the wrapped title and the source line."""
        width, height = cls.HEADLINE_SIZE
        stripe = cls.STRIPES.get(tag, Theme.ACCENT)
        border = Theme.ACCENT if selected else Theme.LINE
        lines = cls.wrap(title, 44, 3)
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
            cls.clip(width, height),
            cls.frame(width, height, border, 2 if selected else 1),
            cls.accent(height, stripe),
            cls.text(20, 22, tag.upper(), 10, stripe, 700, spacing=1.2),
        ]
        parts += [cls.text(20, 42 + 17 * index, line, 13, Theme.NAVY, 600) for index, line in enumerate(lines)]
        parts += [cls.text(20, height - 12, cls.shorten(footer, 52), 11, Theme.MUTED), "</svg>"]
        return cls.data_uri("".join(parts))

    @classmethod
    def hub(cls, name: str, count_text: str, share_text: str) -> str:
        """The hub circle with the current view's name, article count and share."""
        size = cls.HUB_SIZE
        middle = size / 2
        lines = cls.wrap(name, 18, 2)
        name_top = middle - 26 - 10 * (len(lines) - 1)
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">',
            f'<circle cx="{middle}" cy="{middle}" r="{middle - 2}" fill="{Theme.NAVY}"/>',
            f'<circle cx="{middle}" cy="{middle}" r="{middle - 10}" fill="none" '
            f'stroke="{Theme.ACCENT}" stroke-width="2" opacity="0.6"/>',
            cls.text(middle, name_top - 22, "CURRENT VIEW", 10, "#AFC3E8", 600, "middle", 1.5),
        ]
        parts += [
            cls.text(middle, name_top + 20 * index, line, 17, "#FFFFFF", 700, "middle")
            for index, line in enumerate(lines)
        ]
        parts += [
            cls.text(middle, middle + 30, count_text, 28, "#FFFFFF", 700, "middle"),
            cls.text(middle, middle + 52, share_text, 12, "#D6E0F5", 400, "middle"),
            "</svg>",
        ]
        return cls.data_uri("".join(parts))
