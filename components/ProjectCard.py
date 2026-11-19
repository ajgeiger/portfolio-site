"""A card that presents one project: thumbnail, summary, real numbers and links."""

import dash
from dash import dcc, html

from portfolio.Project import Project


class ProjectCard:
    """Build a project card. The featured layout puts the image beside the text."""

    def build(self, project: Project, highlights: list[tuple[str, str]], featured: bool = False) -> html.Article:
        image = dcc.Link(
            html.Img(src=dash.get_asset_url(project.thumbnail), alt=f"Screenshot of {project.title}"),
            href=project.route,
            className="project-image",
        )
        stats = html.Div(
            [
                html.Div(
                    [html.Div(value, className="stat-value"), html.Div(label, className="stat-label")], className="stat"
                )
                for value, label in highlights
            ],
            className="project-stats",
        )
        actions = html.Div(
            [
                dcc.Link("Open the live project \u2192", href=project.route, className="button primary"),
                html.A(
                    project.repo_label,
                    href=project.repo_url,
                    target="_blank",
                    rel="noopener noreferrer",
                    className="button",
                ),
            ],
            className="project-actions",
        )
        body = html.Div(
            [
                html.Div([html.Span(tag, className="tag-pill") for tag in project.tags], className="tag-row"),
                html.H3(dcc.Link(project.title, href=project.route), className="project-title"),
                html.P(project.summary, className="project-summary"),
                stats,
                actions,
            ],
            className="project-body",
        )
        return html.Article([image, body], className="project-card" + (" featured" if featured else ""))
