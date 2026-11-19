"""One line item on the resume: a degree, a certification or an award."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeItem:
    """A title, an optional detail after it, the date text and any bullets."""

    title: str
    dates: str
    detail: str = ""
    bullets: tuple[str, ...] = ()

    @property
    def heading(self) -> str:
        return " | ".join(part for part in (self.title, self.detail) if part)
