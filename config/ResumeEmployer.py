"""One employer block on the resume."""

from dataclasses import dataclass

from config.ResumeRole import ResumeRole


@dataclass(frozen=True)
class ResumeEmployer:
    """An employer heading (name, location, overall dates) and the roles held there, newest first."""

    name: str
    roles: tuple[ResumeRole, ...]
    location: str = ""
    dates: str = ""

    @property
    def heading(self) -> str:
        return " | ".join(part for part in (self.name, self.location) if part)
