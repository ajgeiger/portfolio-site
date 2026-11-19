"""The case study introduction shown above a live project."""

from dash import dcc, html

from portfolio.Project import Project


class CaseStudyHeader:
    """The question as the lead, then the data, the approach and key findings in plain words."""

    def build(
        self,
        project: Project,
        highlights: list[tuple[str, str]],
        findings: list[str],
        live_anchor: str,
        live_label: str = "Jump to the live explorer",
    ) -> html.Section:
        crumbs = html.Nav(
            [
                dcc.Link("Projects", href="/projects"),
                html.Span("\u203a", className="crumb-separator"),
                html.Span(project.title),
            ],
            className="case-crumbs",
            **{"aria-label": "Breadcrumb"},
        )
        intro = html.Div(
            [
                crumbs,
                html.Div("CASE STUDY", className="eyebrow"),
                html.H1(project.title, className="page-title"),
                html.P(project.question, className="case-lead"),
                html.Div([html.Span(tag, className="tag-pill") for tag in project.tags], className="tag-row"),
                html.Div(
                    [
                        html.A(f"{live_label} \u2193", href=f"#{live_anchor}", className="button primary"),
                        html.A(
                            project.repo_label,
                            href=project.repo_url,
                            target="_blank",
                            rel="noopener noreferrer",
                            className="button",
                        ),
                    ],
                    className="project-actions",
                ),
            ],
            className="case-intro",
        )
        stats = html.Div(
            [
                html.Div(
                    [html.Div(value, className="stat-value"), html.Div(label, className="stat-label")], className="stat"
                )
                for value, label in highlights
            ],
            className="case-stats",
        )
        blocks = html.Div(
            [
                self.block("The data", project.data),
                self.block("The approach", project.approach),
            ],
            className="case-blocks",
        )
        findings_block = html.Div(
            [html.H2("Key findings", className="section-title small"), html.Ol([html.Li(item) for item in findings])],
            className="case-findings",
        )
        return html.Section([intro, stats, blocks, findings_block], className="case-study")

    @staticmethod
    def block(title: str, text: str) -> html.Div:
        return html.Div([html.H3(title), html.P(text)], className="case-block")
