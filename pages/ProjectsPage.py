"""The projects index, built from the project registry."""

from dash import Dash, html

from components.ProjectCard import ProjectCard
from config.Profile import Profile
from pages.AbstractPage import AbstractPage
from portfolio.ProjectRegistry import ProjectRegistry


class ProjectsPage(AbstractPage):
    """List every registered project as a card."""

    path = "/projects"
    name = "Projects"
    title = "Projects"
    description = "Live analytics and machine learning projects by Alex Geiger."

    def __init__(self, registry: ProjectRegistry):
        self.registry = registry
        self.cards = ProjectCard()

    def layout(self):
        heading = html.Div(
            [
                html.Div("PROJECTS", className="eyebrow"),
                html.H1("Live projects on real data", className="page-title"),
                html.P(
                    "Each project answers one question with a working app, a short case study and the code behind it.",
                    className="section-lead",
                ),
            ],
            className="page-heading",
        )
        cards = [self.cards.build(page.project, page.highlights()) for page in self.registry.pages()]
        more = html.P(
            [
                "More of my code lives on ",
                html.A("GitHub", href=Profile.GITHUB_URL, target="_blank", rel="noopener noreferrer"),
                ".",
            ],
            className="section-lead",
        )
        return html.Div(
            html.Section(
                html.Div([heading, html.Div(cards, className="project-grid"), more], className="section-inner"),
                className="section",
            ),
            className="site-page",
        )

    def register_callbacks(self, app: Dash) -> None:
        """The projects index is static, so it has no callbacks."""
