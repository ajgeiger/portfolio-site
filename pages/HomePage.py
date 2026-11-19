"""The home page: who Alex is, how he works, and why the projects are worth a look."""

from dash import Dash, dcc, html

from components.ProjectCard import ProjectCard
from config.Profile import Profile
from pages.AbstractPage import AbstractPage
from portfolio.ProjectRegistry import ProjectRegistry


class HomePage(AbstractPage):
    """Hero, background, featured projects, way of working, about and contact."""

    path = "/"
    name = "Home"
    title = Profile.ROLE
    description = "Analytics and machine learning projects by Alex Geiger, Lead Data Scientist."

    WAYS_OF_WORKING = [
        (
            "From raw data to decisions",
            "Each project starts with a business question and ends with an answer a reader can act on, not a model "
            "score. The data pipeline, the model and the interface are all part of the work.",
        ),
        (
            "Honest method notes",
            "Every number says what it counts and what it leaves out. Unassigned records, odd dates and duplicates "
            "are shown and explained rather than quietly dropped.",
        ),
        (
            "Production style code",
            "Small, readable classes, one per file, with tests and linting. Data sources and pages plug in, so a new "
            "dataset or project does not mean a rewrite.",
        ),
    ]

    def __init__(self, registry: ProjectRegistry):
        self.registry = registry
        self.cards = ProjectCard()

    def layout(self):
        return html.Div(
            [self.hero(), self.background(), self.featured(), self.way_of_working(), self.about()],
            className="site-page",
        )

    def hero(self) -> html.Section:
        first_project = self.registry.projects[0]
        return html.Section(
            html.Div(
                [
                    html.Div(Profile.ROLE.upper(), className="eyebrow light"),
                    html.H1("I turn large, messy data into decisions people can act on.", className="hero-title"),
                    html.P(
                        "I build analytics end to end: data engineering, forecasting, pricing and machine learning "
                        "that runs in production under proper governance. This site shows that way of working on open "
                        "data, with live projects you can explore and the code behind them.",
                        className="hero-lead",
                    ),
                    html.Div(
                        [
                            dcc.Link("Explore the projects \u2192", href="/projects", className="button primary large"),
                            dcc.Link(
                                f"Open the {first_project.title}",
                                href=first_project.route,
                                className="button ghost large",
                            ),
                        ],
                        className="hero-actions",
                    ),
                ],
                className="hero-inner",
            ),
            className="hero",
        )

    def background(self) -> html.Section:
        areas = ", ".join(Profile.PLATFORM_AREAS[:-1]) + " and " + Profile.PLATFORM_AREAS[-1]
        items = [
            ("Role", Profile.ROLE, "Leading data science from problem framing to deployed systems."),
            (
                "Enterprise AI platform",
                "Signature Aviation",
                f"Built and led the company's enterprise AI platform, covering {areas}.",
            ),
            ("Education", "Syracuse University", f"{Profile.EDUCATION}."),
        ]
        cards = [
            html.Div(
                [html.Div(label, className="credential-label"), html.H3(heading), html.P(text)], className="credential"
            )
            for label, heading, text in items
        ]
        return html.Section(
            html.Div(
                [html.H2("Background", className="section-title"), html.Div(cards, className="credential-grid")],
                className="section-inner",
            ),
            className="section",
        )

    def featured(self) -> html.Section:
        cards = [self.cards.build(page.project, page.highlights(), featured=True) for page in self.registry.pages()]
        heading = html.Div(
            [
                html.Div("FEATURED WORK", className="eyebrow"),
                html.H2("Projects you can use, not just read about", className="section-title"),
                html.P(
                    "Each project is a working app on real data, with a short case study and method notes. "
                    "The numbers below are read from the data when the site starts.",
                    className="section-lead",
                ),
            ]
        )
        return html.Section(html.Div([heading, *cards], className="section-inner"), className="section tinted")

    def way_of_working(self) -> html.Section:
        steps = [
            html.Div(
                [html.Div(f"0{index}", className="step-number"), html.H3(title), html.P(text)], className="way-card"
            )
            for index, (title, text) in enumerate(self.WAYS_OF_WORKING, start=1)
        ]
        return html.Section(
            html.Div(
                [
                    html.Div("WHAT YOU WILL SEE", className="eyebrow"),
                    html.H2("How I work", className="section-title"),
                    html.Div(steps, className="way-grid"),
                    html.Div(
                        dcc.Link("See all projects \u2192", href="/projects", className="button primary"),
                        className="center-actions",
                    ),
                ],
                className="section-inner",
            ),
            className="section",
        )

    def about(self) -> html.Section:
        areas = ", ".join(Profile.PLATFORM_AREAS[:-1]) + " and " + Profile.PLATFORM_AREAS[-1]
        about = html.Div(
            [
                html.H2("About", className="section-title"),
                html.P(
                    f"I am {Profile.NAME}, a {Profile.ROLE.lower()}. At Signature Aviation I built and led the "
                    f"enterprise AI platform, covering {areas}. I studied data science at the graduate level at "
                    "Syracuse University."
                ),
                html.P(
                    "This portfolio applies the same habits to open data: clear questions, careful method notes and "
                    "code that is built to last."
                ),
            ],
            id="about",
            className="about-block",
        )
        contact = html.Div(
            [
                html.H2("Contact", className="section-title"),
                html.P("The quickest way to see more of my work or get in touch is through these profiles."),
                html.Div(
                    [
                        html.A(
                            "GitHub \u2197",
                            href=Profile.GITHUB_URL,
                            target="_blank",
                            rel="noopener noreferrer",
                            className="button primary",
                        ),
                        html.A(
                            "Kaggle \u2197",
                            href=Profile.KAGGLE_URL,
                            target="_blank",
                            rel="noopener noreferrer",
                            className="button",
                        ),
                    ],
                    className="project-actions",
                ),
            ],
            id="contact",
            className="about-block",
        )
        return html.Section(
            html.Div([about, contact], className="section-inner about-grid"), className="section tinted"
        )

    def register_callbacks(self, app: Dash) -> None:
        """The home page is static, so it has no callbacks."""
