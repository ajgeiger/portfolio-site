"""The panel to the right of the graph that explains the current view."""

from dash import html

from components.ExplorerIds import ExplorerIds
from config.Formats import Formats


class SidePanel:
    """Show what the selected node is, how big it is and what it contains."""

    def build(self, details: dict) -> list:
        """Build the panel from a dictionary prepared by the page.

        Expected keys: kind, name, keyword_name, renamed, count, share, share_label,
        parent_share, parent_name, keywords, largest_topics, examples, article.
        """
        sections = []
        if details.get("article"):
            sections.append(self.article_detail(details["article"]))
        sections += [
            html.Div(details["kind"].upper(), className=f"kind-badge kind-{details['kind'].split()[0].lower()}"),
            html.H3(details["name"], className="side-title"),
        ]
        if details["renamed"]:
            sections.append(html.Div(f"Keyword name: {details['keyword_name']}", className="side-subtle"))
        sections.append(self.stats(details))
        if details["keywords"]:
            sections.append(self.section("Keywords behind the label", self.chips(details["keywords"])))
        if details["largest_topics"]:
            sections.append(self.section("Largest topics in this group", self.topic_list(details["largest_topics"])))
        if details["examples"]:
            sections.append(self.section("Example headlines", self.example_list(details["examples"])))
        return sections

    @staticmethod
    def section(title: str, body) -> html.Div:
        return html.Div([html.Div(title, className="side-section-title"), body], className="side-section")

    @staticmethod
    def stats(details: dict) -> html.Div:
        items = [
            html.Div(
                [
                    html.Div(Formats.count(details["count"]), className="stat-value"),
                    html.Div("articles", className="stat-label"),
                ],
                className="stat",
            ),
            html.Div(
                [
                    html.Div(Formats.percent(details["share"]), className="stat-value"),
                    html.Div(details["share_label"], className="stat-label"),
                ],
                className="stat",
            ),
        ]
        if details.get("parent_name"):
            items.append(
                html.Div(
                    [
                        html.Div(Formats.percent(details["parent_share"]), className="stat-value"),
                        html.Div(f"of {details['parent_name']}", className="stat-label"),
                    ],
                    className="stat",
                )
            )
        return html.Div(items, className="stat-row")

    @staticmethod
    def chips(keywords: list[str]) -> html.Div:
        return html.Div([html.Span(word, className="chip") for word in keywords], className="chip-row")

    @staticmethod
    def topic_list(topics: list[dict]) -> html.Div:
        rows = []
        for topic in topics:
            rows.append(
                html.Button(
                    [
                        html.Span(topic["kicker"], className="topic-link-kicker"),
                        html.Span(topic["name"], className="topic-link-name"),
                        html.Span(Formats.count(topic["count"]), className="topic-link-count"),
                    ],
                    id={"type": ExplorerIds.TOPIC_LINK, "key": topic["key"]},
                    className="topic-link",
                    n_clicks=0,
                )
            )
        return html.Div(rows, className="topic-list")

    @staticmethod
    def example_list(examples: list[dict]) -> html.Div:
        rows = []
        for example in examples:
            rows.append(
                html.Button(
                    [
                        html.Span(example["tag"], className=f"tag tag-{example['tag'].lower()}"),
                        html.Span(example["title"], className="example-title"),
                        html.Span(
                            f"{example['source']} \u00b7 {Formats.date(example['published_at'])}",
                            className="example-meta",
                        ),
                    ],
                    id={"type": ExplorerIds.HEADLINE_LINK, "id": example["id"]},
                    className="example",
                    n_clicks=0,
                )
            )
        return html.Div(rows, className="example-list")

    @staticmethod
    def article_detail(article: dict) -> html.Div:
        body = [
            html.Div("SELECTED HEADLINE", className="side-section-title"),
            html.H4(article["title"] or "Untitled article", className="article-title"),
        ]
        if article.get("summary"):
            body.append(html.P(article["summary"], className="article-summary"))
        body.append(
            html.Div(
                f"{article['source']} \u00b7 {Formats.date_time(article['published_at'])} "
                f"\u00b7 {article['source_type'].upper()} feed",
                className="article-meta",
            )
        )
        if article.get("date_flag") in ("stale", "future"):
            body.append(html.Div(f"Note: this publish date looks {article['date_flag']}.", className="article-flag"))
        if article.get("url"):
            body.append(
                html.A(
                    "Open the article \u2197",
                    href=article["url"],
                    target="_blank",
                    rel="noopener noreferrer",
                    className="article-link",
                )
            )
        return html.Div(body, className="article-detail")
