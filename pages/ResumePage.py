"""The resume page: a plain summary of the resume with a link to the PDF."""

from dash import Dash, html

from components.ResumeLink import ResumeLink
from config.Position import Position
from config.Profile import Profile
from config.Resume import Resume
from pages.AbstractPage import AbstractPage


class ResumePage(AbstractPage):
    """Experience, education, certifications and skills, drawn only from the resume."""

    path = "/resume"
    name = "Resume"
    title = "Resume"
    description = "Resume of Alex Geiger, Lead Applied AI Scientist."

    def layout(self):
        heading = html.Div(
            [
                html.Div("RESUME", className="eyebrow"),
                html.H1(Profile.NAME, className="page-title"),
                html.P(f"{Profile.ROLE}, {Profile.EMPLOYER}", className="resume-role"),
                html.P(Resume.SUMMARY, className="section-lead"),
                html.Div(ResumeLink().build("button primary"), className="project-actions"),
            ],
            className="page-heading",
        )
        experience = self.section(
            "Experience",
            [self.position(position) for position in Resume.EXPERIENCE]
            + [html.H3("Earlier experience", className="resume-subheading")]
            + [self.position(position) for position in Resume.EARLIER_EXPERIENCE],
        )
        education = self.section(
            "Education", [self.entry(school, degree, years) for school, degree, years in Resume.EDUCATION]
        )
        certifications = self.section(
            "Certifications", [self.entry(name, "", issued) for name, issued in Resume.CERTIFICATIONS]
        )
        achievements = self.section(
            "Competitions", [self.entry(name, detail, when) for name, when, detail in Resume.ACHIEVEMENTS]
        )
        skills = self.section(
            "Skills",
            [
                html.Div([html.Span(label, className="resume-skill-label"), html.Span(items)], className="resume-skill")
                for label, items in Resume.SKILLS
            ],
        )
        side = html.Div([education, certifications, achievements, skills], className="resume-side")
        body = html.Div([experience, side], className="resume-grid")
        return html.Div(
            html.Section(html.Div([heading, body], className="section-inner"), className="section"),
            className="site-page",
        )

    @staticmethod
    def section(title: str, children: list) -> html.Div:
        return html.Div([html.H2(title, className="section-title small"), *children], className="resume-section")

    @staticmethod
    def position(position: Position) -> html.Div:
        header = html.Div(
            [
                html.Div(
                    [
                        html.H3(position.title, className="resume-title"),
                        html.Div(f"{position.organization}, {position.location}", className="resume-meta"),
                    ]
                ),
                html.Div(position.dates, className="resume-dates"),
            ],
            className="resume-entry-header",
        )
        highlights = [html.Ul([html.Li(item) for item in position.highlights])] if position.highlights else []
        return html.Div([header, *highlights], className="resume-entry")

    @staticmethod
    def entry(title: str, detail: str, when: str) -> html.Div:
        lines = [html.H3(title, className="resume-title"), html.Div(when, className="resume-dates")]
        if detail:
            lines.insert(1, html.Div(detail, className="resume-meta"))
        return html.Div(lines, className="resume-entry compact")

    def register_callbacks(self, app: Dash) -> None:
        """The resume page is static, so it has no callbacks."""
