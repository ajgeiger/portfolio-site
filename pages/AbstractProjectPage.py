"""The contract for a page that presents one project."""

from abc import abstractmethod

from pages.AbstractPage import AbstractPage
from portfolio.Project import Project


class AbstractProjectPage(AbstractPage):
    """A project page lives at /projects/<slug> and can summarize itself for cards."""

    def __init__(self, project: Project):
        self.project = project
        self.path = project.route
        self.name = project.title
        self.title = project.title
        self.description = project.summary

    @property
    def module_name(self) -> str:
        return f"pages.projects.{self.project.slug}"

    @abstractmethod
    def highlights(self) -> list[tuple[str, str]]:
        """Headline numbers read from the project's data, as (value, label) pairs."""
