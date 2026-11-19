"""The resume page: the full resume as a clean web document, with the PDF one click away."""

from dash import Dash, html

from components.ResumeLink import ResumeLink
from config.Resume import Resume
from config.ResumeEmployer import ResumeEmployer
from config.ResumeItem import ResumeItem
from config.ResumeRole import ResumeRole
from pages.AbstractPage import AbstractPage


class ResumePage(AbstractPage):
    """Every section and bullet of the resume, in the same order as the PDF.

    The text comes from config/Resume.py. The phone number and personal email
    are only in the downloadable PDF, never in the page text.
    """

    path = "/resume"
    name = "Resume"
    title = "Resume"
    description = "Resume of Alexander J. Geiger, Lead Applied AI Scientist."

    def layout(self):
        toolbar = html.Div(
            [
                html.Div(
                    [html.Div("RESUME", className="eyebrow"), html.P("Web version of the PDF.", className="muted")]
                ),
                ResumeLink().build("button primary large"),
            ],
            className="resume-toolbar",
        )
        document = html.Article(
            [
                self.header(),
                self.section(Resume.SUMMARY_TITLE, [html.P(Resume.SUMMARY, className="resume-summary")]),
                self.section(Resume.SKILLS_TITLE, [self.skills()]),
                self.section(Resume.EXPERIENCE_TITLE, [self.employer(employer) for employer in Resume.EXPERIENCE]),
                self.section(Resume.EDUCATION_TITLE, [self.item(item) for item in Resume.EDUCATION]),
                self.section(Resume.CERTIFICATIONS_TITLE, [self.item(item) for item in Resume.CERTIFICATIONS]),
                self.section(Resume.ACHIEVEMENTS_TITLE, [self.item(item) for item in Resume.ACHIEVEMENTS]),
                html.Div(ResumeLink().build("button primary"), className="resume-doc-footer"),
            ],
            className="resume-doc",
        )
        return html.Div(html.Div([toolbar, document], className="resume-page"), className="site-page")

    # Building blocks

    @staticmethod
    def header() -> html.Header:
        links = []
        for index, (label, url) in enumerate(Resume.LINKS):
            if index:
                links.append(html.Span("\u2022", className="resume-dot"))
            links.append(html.A(label, href=url, target="_blank", rel="noopener noreferrer"))
        return html.Header(
            [
                html.H1(Resume.NAME, className="resume-name"),
                html.Div(Resume.HEADLINE, className="resume-headline"),
                html.Div(Resume.LOCATION, className="resume-location"),
                html.Div(links, className="resume-links"),
            ],
            className="resume-header",
        )

    @staticmethod
    def section(title: str, children: list) -> html.Section:
        return html.Section([html.H2(title, className="resume-section-title"), *children], className="resume-block")

    @staticmethod
    def skills() -> html.Dl:
        rows = []
        for label, value in Resume.SKILLS:
            rows += [html.Dt(label), html.Dd(value)]
        return html.Dl(rows, className="resume-skills")

    @staticmethod
    def row(left, right: str, class_name: str) -> html.Div:
        """A line with text on the left and dates aligned to the right."""
        return html.Div(
            [html.Div(left, className="resume-row-left"), html.Div(right, className="resume-row-dates")],
            className=f"resume-row {class_name}",
        )

    @staticmethod
    def bullets(items: tuple[str, ...]) -> list:
        return [html.Ul([html.Li(item) for item in items], className="resume-bullets")] if items else []

    def employer(self, employer: ResumeEmployer) -> html.Div:
        name = [html.Span(employer.name, className="resume-employer-name")]
        if employer.location:
            name += [
                html.Span("|", className="resume-separator"),
                html.Span(employer.location, className="resume-place"),
            ]
        return html.Div(
            [self.row(name, employer.dates, "employer"), *[self.role(role) for role in employer.roles]],
            className="resume-employer",
        )

    def role(self, role: ResumeRole) -> html.Div:
        note = [html.P(role.note, className="resume-note")] if role.note else []
        return html.Div(
            [self.row(role.heading, role.dates, "role"), *note, *self.bullets(role.bullets)],
            className="resume-role-block",
        )

    def item(self, item: ResumeItem) -> html.Div:
        heading = [html.Span(item.title, className="resume-item-title")]
        if item.detail:
            heading += [html.Span("|", className="resume-separator"), html.Span(item.detail)]
        return html.Div([self.row(heading, item.dates, "item"), *self.bullets(item.bullets)], className="resume-item")

    def register_callbacks(self, app: Dash) -> None:
        """The resume page is static, so it has no callbacks."""
