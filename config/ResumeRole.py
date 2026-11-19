"""One role on the resume."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeRole:
    """A job title with its dates, an optional note and the bullets as written on the resume.

    Roles listed under Earlier Experience carry their own organization and
    location, because they are not grouped under an employer heading.
    """

    title: str
    dates: str
    bullets: tuple[str, ...] = ()
    note: str = ""
    organization: str = ""
    location: str = ""

    @property
    def heading(self) -> str:
        """The role line as the resume prints it, for example "Soleo | Data Scientist Intern | Rochester, NY"."""
        return " | ".join(part for part in (self.organization, self.title, self.location) if part)
