"""One role on the resume."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """A role at one organization, with the dates and a few highlights taken from the resume."""

    title: str
    organization: str
    location: str
    dates: str
    highlights: tuple[str, ...] = ()
