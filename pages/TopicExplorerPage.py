"""The topic explorer: what is the news talking about, and how much coverage does each theme get?"""

import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, callback_context, dcc, html, no_update

from analytics.ArticleFilter import ArticleFilter
from analytics.CoverageSummary import CoverageSummary
from analytics.ExplorerQuery import ExplorerQuery
from analytics.InsightWriter import InsightWriter
from analytics.LabelStore import LabelStore
from analytics.RisingTopics import RisingTopics
from analytics.SourceMix import SourceMix
from analytics.TopicSearch import TopicSearch
from analytics.TopicTrend import TopicTrend
from components.CardSvg import CardSvg
from components.CaseStudyHeader import CaseStudyHeader
from components.ExplorerIds import ExplorerIds as Ids
from components.FilterBar import FilterBar
from components.MethodNotesModal import MethodNotesModal
from components.NavigationBar import NavigationBar
from components.RisingChart import RisingChart
from components.SidePanel import SidePanel
from components.SourceMixChart import SourceMixChart
from components.SummaryCards import SummaryCards
from components.TopicGraph import TopicGraph
from components.TrendChart import TrendChart
from config.Formats import Formats
from config.Settings import Settings
from config.Theme import Theme
from data.AbstractDataSource import AbstractDataSource
from pages.AbstractProjectPage import AbstractProjectPage
from portfolio.Project import Project


class TopicExplorerPage(AbstractProjectPage):
    """Start from every article and drill down one level at a time to real headlines.

    The page state is a breadcrumb path of node keys plus an optional selected
    article. Every callback reads the same filters, so cards, graph, side panel
    and charts always describe the same set of articles.
    """

    EXPLORER_ANCHOR = "explorer"

    GRAPH_HINT = (
        "Click a card to go one level down. Drag to move, scroll or use + and \u2212 to zoom. "
        "Positions and curves are for reading only."
    )

    GRANULARITY_NAMES = {"hour": "Hourly", "day": "Daily", "week": "Weekly"}

    FILTER_INPUTS = [
        Input(Ids.DATE_RANGE, "start_date"),
        Input(Ids.DATE_RANGE, "end_date"),
        Input(Ids.SOURCE_TYPES, "value"),
        Input(Ids.SOURCES, "value"),
    ]

    def __init__(self, project: Project, data_source: AbstractDataSource, settings: Settings | None = None):
        super().__init__(project)
        self.settings = settings or Settings()
        self.query = ExplorerQuery(data_source, self.settings.random_state)
        self.search_index = TopicSearch(data_source.tree())
        self.trend = TopicTrend(self.query.last_load_time, published=self.query.articles["published_at"])
        self.rising = RisingTopics(self.query.last_load_time)
        self.graph = TopicGraph()
        self.side_panel = SidePanel()
        self.navigation = NavigationBar()
        self.summary_cards = SummaryCards()
        self.insight_writer = InsightWriter()

    # Layout

    def layout(self):
        """Header, filters, summary cards, graph with side panel, time and source charts, rising topics."""
        return html.Div(
            [
                dcc.Store(id=Ids.VIEW_STATE, data=self.start_state()),
                dcc.Store(id=Ids.LABELS, data={}, storage_type="memory"),
                dcc.Download(id=Ids.DOWNLOAD),
                CaseStudyHeader().build(self.project, self.highlights(), self.key_findings(), self.EXPLORER_ANCHOR),
                self.header(),
                FilterBar().build(
                    self.query.articles,
                    self.query.last_load_time,
                    self.settings.branch_choices,
                    self.settings.default_branches,
                ),
                html.Div(id=Ids.SUMMARY_CARDS, className="summary-cards"),
                html.Div(
                    [
                        html.Div(
                            [
                                self.navigation.build(),
                                self.graph.component(Ids.GRAPH),
                                html.Div(self.GRAPH_HINT, className="graph-hint"),
                            ],
                            className="panel graph-panel",
                        ),
                        html.Aside([html.Div(id=Ids.SIDE_PANEL), self.rename_block()], className="panel side-panel"),
                    ],
                    className="main-grid",
                ),
                html.Div(
                    [
                        self.chart_panel(
                            "Coverage over time",
                            html.Div(id=Ids.SELECTION_TITLE),
                            self.segmented(
                                Ids.TREND_GRANULARITY,
                                [("Auto", "auto"), ("Hourly", "hour"), ("Daily", "day"), ("Weekly", "week")],
                            ),
                            Ids.TREND_CHART,
                            Ids.TREND_NOTE,
                        ),
                        self.chart_panel(
                            "Source mix",
                            "Which outlets cover the current view",
                            None,
                            Ids.SOURCE_CHART,
                            Ids.SOURCE_NOTE,
                        ),
                    ],
                    className="lower-grid",
                ),
                self.chart_panel(
                    "Rising and fading topics",
                    "Change in share of coverage. Click a bar to open the topic.",
                    self.segmented(
                        Ids.RISING_WINDOW,
                        [("Auto", "auto")] + [(window.key, window.key) for window in RisingTopics.WINDOWS],
                    ),
                    Ids.RISING_CHART,
                    Ids.RISING_NOTE,
                    class_name="panel rising-panel",
                ),
                MethodNotesModal().build(self.query.metadata),
            ],
            className="explorer project-page",
        )

    def header(self) -> html.Section:
        """The title row of the live explorer, with the insight line and the method notes button."""
        metadata = self.query.metadata
        subtitle = (
            "Start from every article and open one theme at a time, down to the headlines. "
            f"Data last loaded {Formats.date_time(metadata['last_load_time'])}."
        )
        intro = html.Div(
            [
                html.Div("LIVE EXPLORER", className="eyebrow"),
                html.H2("Explore the coverage yourself", className="section-title"),
                html.P(subtitle, className="page-subtitle"),
                html.Div(id=Ids.INSIGHT, className="insight"),
            ],
            className="page-intro",
        )
        notes_button = html.Button("How to read this", id=Ids.NOTES_OPEN, className="notes-button", n_clicks=0)
        return html.Section([intro, notes_button], className="page-header", id=self.EXPLORER_ANCHOR)

    # Project summary

    def highlights(self) -> list[tuple[str, str]]:
        metadata = self.query.metadata
        summary = CoverageSummary.from_articles(self.query.articles)
        return [
            (Formats.count(metadata["article_rows"]), "news articles"),
            (Formats.count(metadata["topic_count"]), "topics found by the model"),
            (Formats.count(self.query.articles["source"].nunique()), "news sources"),
            (Formats.percent(summary.unassigned_share), "shown as unassigned, not hidden"),
        ]

    def key_findings(self) -> list[str]:
        """Plain language findings, computed from the data each time the app starts."""
        articles = self.query.articles
        metadata = self.query.metadata
        summary = CoverageSummary.from_articles(articles)
        counts = self.query.topic_counts(articles)
        themes = self.query.branch_keys(ExplorerQuery.ASSIGNED, self.settings.default_branches, counts, summary)
        theme_counts = [self.query.count(theme, counts, summary) for theme in themes]
        top_share = Formats.percent(summary.share(theme_counts[0], summary.rows_with_text))
        top_three_share = Formats.percent(summary.share(sum(theme_counts[:3]), summary.rows_with_text))
        repeat_share = Formats.percent(metadata["repeat_text_rows"] / max(metadata["article_rows"], 1))
        findings = [
            f"Coverage splits into {len(themes)} broad themes. The largest, keyword labeled "
            f"\u201c{self.query.keyword_name(themes[0])}\u201d, holds {top_share} of articles with text, "
            f"and the three largest together hold {top_three_share}, so no single theme dominates.",
            f"{Formats.percent(summary.unassigned_share)} of articles with text fit no topic: one off or vague "
            "stories. The explorer counts them openly instead of dropping them.",
            f"{repeat_share} of rows repeat a headline that already appears, mostly syndicated copies, so counts "
            "measure coverage rather than unique stories.",
        ]
        rising_finding = self.rising_finding(articles)
        return findings + ([rising_finding] if rising_finding else [])

    def rising_finding(self, articles) -> str | None:
        """Describe the fastest rising topic, and say so plainly when it is one syndicated headline."""
        window = self.rising.choose_window(articles)
        rising = self.rising.compare(articles, window)
        if not len(rising) or rising.iloc[0]["change_points"] <= 0:
            return None
        topic = int(rising.iloc[0]["topic_id"])
        rows = articles[articles["topic_id"] == topic]
        period = window.label.split(" vs ")[0].lower()
        if rows["title"].nunique() == 1:
            source_count = rows["source"].nunique()
            outlets = "a single outlet" if source_count == 1 else Formats.amount(source_count, "outlet")
            return (
                f"The fastest rising topic over the {period} is a single headline repeated "
                f"{Formats.count(len(rows))} times by {outlets}. Rising share can mean wide syndication, "
                "not a developing story."
            )
        name = self.query.keyword_name(self.query.tree.topic_key(topic))
        change = Formats.points(float(rising.iloc[0]["change_points"]))
        return f"The fastest rising topic over the {period} is \u201c{name}\u201d, up {change} of share."

    @staticmethod
    def chart_panel(title, subtitle, control, chart_id: str, note_id: str, class_name: str = "panel") -> html.Div:
        """A titled panel with an optional control on the right, a chart and a note below it."""
        heading = html.Div([html.H3(title), html.Div(subtitle, className="panel-subtitle")])
        header = html.Div([heading, control] if control is not None else [heading], className="panel-header")
        chart = dcc.Graph(id=chart_id, config={"displayModeBar": False})
        return html.Div([header, chart, html.Div(id=note_id, className="panel-note")], className=class_name)

    @staticmethod
    def segmented(component_id: str, choices: list[tuple[str, str]]) -> dcc.RadioItems:
        options = [{"label": label, "value": value} for label, value in choices]
        return dcc.RadioItems(id=component_id, options=options, value=choices[0][1], inline=True, className="segmented")

    @staticmethod
    def rename_block() -> html.Div:
        return html.Div(
            [
                html.Div("Rename this label", className="side-section-title"),
                html.Div(id=Ids.RENAME_TARGET, className="side-subtle"),
                html.Div(
                    [
                        dcc.Input(
                            id=Ids.RENAME_INPUT, type="text", debounce=False, className="rename-input", n_submit=0
                        ),
                        html.Button("Apply", id=Ids.RENAME_APPLY, className="nav-button primary", n_clicks=0),
                        html.Button("Reset", id=Ids.RENAME_RESET, className="nav-button", n_clicks=0),
                    ],
                    className="rename-row",
                ),
                html.Div(
                    [
                        html.Span(id=Ids.RENAME_COUNT, className="side-subtle"),
                        html.Button("Export JSON", id=Ids.EXPORT_JSON, className="nav-button", n_clicks=0),
                        html.Button("Export CSV", id=Ids.EXPORT_CSV, className="nav-button", n_clicks=0),
                    ],
                    className="export-row",
                ),
            ],
            className="rename-block",
        )

    def start_state(self) -> dict:
        return {"path": [ExplorerQuery.ALL], "article": None}

    # Callbacks

    def register_callbacks(self, app: Dash) -> None:
        app.callback(
            Output(Ids.VIEW_STATE, "data"),
            Output(Ids.SEARCH, "value"),
            Input(Ids.GRAPH, "tapNode"),
            Input({"type": Ids.SUMMARY_CARD, "key": ALL}, "n_clicks"),
            Input(Ids.BACK, "n_clicks"),
            Input(Ids.HOME, "n_clicks"),
            Input({"type": Ids.CRUMB, "index": ALL}, "n_clicks"),
            Input({"type": Ids.TOPIC_LINK, "key": ALL}, "n_clicks"),
            Input({"type": Ids.HEADLINE_LINK, "id": ALL}, "n_clicks"),
            Input(Ids.SEARCH, "value"),
            Input(Ids.RISING_CHART, "clickData"),
            State(Ids.VIEW_STATE, "data"),
            State(Ids.BRANCHES, "value"),
            prevent_initial_call=True,
        )(self.navigate)

        app.callback(
            Output(Ids.GRAPH, "elements"),
            Output(Ids.SIDE_PANEL, "children"),
            Output(Ids.BREADCRUMBS, "children"),
            Output(Ids.SUMMARY_CARDS, "children"),
            Output(Ids.INSIGHT, "children"),
            Output(Ids.BACK, "disabled"),
            Output(Ids.RENAME_INPUT, "value"),
            Output(Ids.RENAME_INPUT, "placeholder"),
            Output(Ids.RENAME_INPUT, "disabled"),
            Output(Ids.RENAME_TARGET, "children"),
            Output(Ids.RENAME_COUNT, "children"),
            Output(Ids.FILTER_NOTE, "children"),
            Output(Ids.SELECTION_TITLE, "children"),
            Input(Ids.VIEW_STATE, "data"),
            *self.FILTER_INPUTS,
            Input(Ids.BRANCHES, "value"),
            Input(Ids.LABELS, "data"),
        )(self.render_view)

        app.callback(
            Output(Ids.TREND_CHART, "figure"),
            Output(Ids.TREND_NOTE, "children"),
            Output(Ids.SOURCE_CHART, "figure"),
            Output(Ids.SOURCE_NOTE, "children"),
            Input(Ids.VIEW_STATE, "data"),
            *self.FILTER_INPUTS,
            Input(Ids.TREND_GRANULARITY, "value"),
        )(self.render_time_and_sources)

        app.callback(
            Output(Ids.RISING_CHART, "figure"),
            Output(Ids.RISING_NOTE, "children"),
            *self.FILTER_INPUTS,
            Input(Ids.RISING_WINDOW, "value"),
            Input(Ids.LABELS, "data"),
        )(self.render_rising)

        app.callback(
            Output(Ids.SEARCH, "options"),
            Input(Ids.SEARCH, "search_value"),
            State(Ids.LABELS, "data"),
        )(self.search_options)

        app.callback(
            Output(Ids.LABELS, "data"),
            Input(Ids.RENAME_APPLY, "n_clicks"),
            Input(Ids.RENAME_INPUT, "n_submit"),
            Input(Ids.RENAME_RESET, "n_clicks"),
            State(Ids.RENAME_INPUT, "value"),
            State(Ids.VIEW_STATE, "data"),
            State(Ids.LABELS, "data"),
            prevent_initial_call=True,
        )(self.rename)

        app.callback(
            Output(Ids.DOWNLOAD, "data"),
            Input(Ids.EXPORT_JSON, "n_clicks"),
            Input(Ids.EXPORT_CSV, "n_clicks"),
            State(Ids.LABELS, "data"),
            prevent_initial_call=True,
        )(self.export_labels)

        app.callback(
            Output(Ids.NOTES_MODAL, "style"),
            Input(Ids.NOTES_OPEN, "n_clicks"),
            Input(Ids.NOTES_CLOSE, "n_clicks"),
            prevent_initial_call=True,
        )(self.toggle_notes)

        app.callback(
            Output(Ids.GRAPH, "zoom"),
            Output(Ids.GRAPH, "layout"),
            Input(Ids.ZOOM_IN, "n_clicks"),
            Input(Ids.ZOOM_OUT, "n_clicks"),
            Input(Ids.FIT, "n_clicks"),
            State(Ids.GRAPH, "zoom"),
            prevent_initial_call=True,
        )(self.control_graph)

    # Navigation

    def navigate(
        self,
        tap_node,
        card_clicks,
        back,
        home,
        crumb_clicks,
        topic_clicks,
        headline_clicks,
        search_value,
        rising_click,
        state,
        branches,
    ):
        trigger = callback_context.triggered_id
        value = callback_context.triggered[0]["value"] if callback_context.triggered else None
        if trigger is None or not value:
            return no_update, no_update
        new_state = self.next_state(
            trigger, value, state or self.start_state(), branches or self.settings.default_branches
        )
        clear_search = None if trigger == Ids.SEARCH else no_update
        return (new_state if new_state is not None else no_update), clear_search

    def next_state(self, trigger, value, state: dict, branches: int) -> dict | None:
        """Work out the new view state from what was clicked. None means nothing changes."""
        path = list(state["path"])
        article = state.get("article")
        kind = trigger.get("type") if isinstance(trigger, dict) else trigger

        if kind == Ids.GRAPH:
            data = value.get("data", {})
            if data.get("kind") == "hub":
                return {"path": path, "article": None} if article else None
            if data.get("kind") == "headline":
                return {"path": path, "article": data["article_id"]}
            return self.open_branch(path, data.get("key"))
        if kind == Ids.SUMMARY_CARD:
            return {"path": self.query.path_to(trigger["key"], branches), "article": None}
        if kind == Ids.BACK:
            if article:
                return {"path": path, "article": None}
            return {"path": path[:-1] or path, "article": None}
        if kind == Ids.HOME:
            return self.start_state()
        if kind == Ids.CRUMB:
            return {"path": path[: trigger["index"] + 1], "article": None}
        if kind == Ids.TOPIC_LINK:
            return {"path": self.query.path_to(trigger["key"], branches), "article": None}
        if kind == Ids.HEADLINE_LINK:
            return {"path": path, "article": trigger["id"]}
        if kind == Ids.SEARCH and self.query.is_known(value):
            return {"path": self.query.path_to(value, branches), "article": None}
        if kind == Ids.RISING_CHART:
            key = value["points"][0].get("customdata")
            if key and self.query.is_known(key):
                return {"path": self.query.path_to(key, branches), "article": None}
        return None

    def open_branch(self, path: list[str], key: str | None) -> dict | None:
        if not key or not self.query.is_known(key):
            return None
        if key in path:
            return {"path": path[: path.index(key) + 1], "article": None}
        return {"path": path + [key], "article": None}

    # Rendering

    def current_key(self, state: dict | None) -> str:
        path = (state or {}).get("path") or [ExplorerQuery.ALL]
        key = path[-1]
        return key if self.query.is_known(key) else ExplorerQuery.ALL

    def render_view(self, state, start_date, end_date, source_types, sources, branches, labels):
        state = state or self.start_state()
        branches = branches or self.settings.default_branches
        label_store = LabelStore(labels)
        article_filter = ArticleFilter.from_inputs(start_date, end_date, source_types, sources)
        articles = self.query.filtered(article_filter)
        summary = CoverageSummary.from_articles(articles)
        counts = self.query.topic_counts(articles)

        path = [key for key in state["path"] if self.query.is_known(key)] or [ExplorerQuery.ALL]
        key = path[-1]
        count = self.query.count(key, counts, summary)
        share = summary.share(count, self.query.share_base(key, summary))
        name = self.query.name(key, label_store)

        elements = self.graph.elements(
            self.hub(key, name, count, share, summary),
            self.branch_cards(key, count, articles, counts, summary, branches, label_store, state.get("article")),
        )
        panel = self.side_panel.build(
            self.panel_details(path, articles, counts, summary, label_store, state.get("article"))
        )
        crumbs = NavigationBar.breadcrumbs([self.query.name(step, label_store) for step in path])
        cards = self.summary_cards.build(summary, key)
        insight = self.insight(articles, counts, summary, label_store)

        can_rename = self.query.tree.has(key)
        rename_value = label_store.labels.get(key, "") if can_rename else ""
        placeholder = self.query.keyword_name(key) if can_rename else "Open a topic or group to rename it"
        target = (
            f"{self.query.kind(key)}: {self.query.keyword_name(key)}"
            if can_rename
            else "Overview views keep their fixed names."
        )
        renamed = len(label_store.labels)
        rename_count = Formats.amount(renamed, "renamed label")
        filter_note = (
            f"Showing {Formats.count(summary.total_rows)} of {Formats.count(len(self.query.articles))} articles"
            if article_filter.is_active()
            else ""
        )
        back_disabled = len(path) == 1 and not state.get("article")
        return (
            elements,
            panel,
            crumbs,
            cards,
            insight,
            back_disabled,
            rename_value,
            placeholder,
            not can_rename,
            target,
            rename_count,
            filter_note,
            name,
        )

    def hub(self, key: str, name: str, count: int, share: float, summary: CoverageSummary) -> dict:
        if key == ExplorerQuery.ALL:
            share_text = "every article in view"
        elif key == ExplorerQuery.MISSING:
            share_text = f"{Formats.percent(share)} of all rows"
        else:
            share_text = f"{Formats.percent(share)} of articles with text"
        return {"key": f"hub::{key}", "image": CardSvg.hub(name, Formats.count(count), share_text)}

    def branch_cards(
        self, key, view_count, articles, counts, summary, branches, label_store, selected_article
    ) -> list[dict]:
        if self.query.shows_headlines(key):
            width, height = CardSvg.HEADLINE_SIZE
            cards = []
            for headline in self.query.headlines(key, articles, branches):
                footer = f"{headline['source']} \u00b7 {Formats.date(headline['published_at'])}"
                cards.append(
                    {
                        "key": f"article::{headline['id']}",
                        "image": CardSvg.headline(
                            headline["tag"], headline["title"], footer, headline["id"] == selected_article
                        ),
                        "width": width,
                        "height": height,
                        "kind": "headline",
                        "article_id": headline["id"],
                    }
                )
            return cards

        width, height = CardSvg.BRANCH_SIZE
        cards = []
        for branch in self.query.branch_keys(key, branches, counts, summary):
            count = self.query.count(branch, counts, summary)
            base = self.query.share_base(branch, summary)
            base_label = "of all rows" if branch == ExplorerQuery.MISSING else "of articles"
            detail = (
                f"{Formats.count(count)} articles \u00b7 {Formats.percent(summary.share(count, base))} {base_label}"
            )
            style = (
                branch
                if branch in (ExplorerQuery.UNASSIGNED, ExplorerQuery.MISSING)
                else ("topic" if self.query.tree.is_topic(branch) else "group")
            )
            cards.append(
                {
                    "key": branch,
                    "image": CardSvg.branch(
                        self.query.kicker(branch),
                        self.query.name(branch, label_store),
                        detail,
                        summary.share(count, view_count),
                        style,
                        label_store.is_renamed(branch),
                    ),
                    "width": width,
                    "height": height,
                    "kind": style,
                }
            )
        return cards

    def panel_details(self, path, articles, counts, summary, label_store, article_id) -> dict:
        key = path[-1]
        count = self.query.count(key, counts, summary)
        base = self.query.share_base(key, summary)
        share_label = {ExplorerQuery.ALL: "of all articles", ExplorerQuery.MISSING: "of all rows"}.get(
            key, "of articles with text"
        )
        details = {
            "kind": self.query.kind(key),
            "name": self.query.name(key, label_store),
            "keyword_name": self.query.keyword_name(key),
            "renamed": label_store.is_renamed(key),
            "count": count,
            "share": summary.share(count, base),
            "share_label": share_label,
            "parent_name": None,
            "parent_share": 0.0,
            "keywords": self.query.keywords(key)[:10],
            "largest_topics": [],
            "examples": self.query.headlines(key, articles, 3),
            "article": self.query.article(article_id) if article_id else None,
        }
        if len(path) > 1:
            parent = path[-2]
            parent_count = self.query.count(parent, counts, summary)
            details["parent_name"] = self.query.name(parent, label_store)
            details["parent_share"] = summary.share(count, parent_count)
        if not self.query.shows_headlines(key):
            details["largest_topics"] = [
                {
                    "key": topic_key,
                    "kicker": self.query.kicker(topic_key).title(),
                    "name": self.query.name(topic_key, label_store),
                    "count": self.query.count(topic_key, counts, summary),
                }
                for topic_key in self.query.largest_topics(key, counts, 8)
            ]
        return details

    def insight(self, articles, counts, summary, label_store) -> list:
        top_theme = None
        theme_keys = [
            key
            for key in self.query.branch_keys(ExplorerQuery.ASSIGNED, self.settings.default_branches, counts, summary)
        ]
        if theme_keys:
            top_theme = (self.query.name(theme_keys[0], label_store), self.query.count(theme_keys[0], counts, summary))
        rising = None
        window = self.rising.choose_window(articles)
        table = self.rising.compare(articles, window)
        if len(table) and table.iloc[0]["change_points"] > 0:
            topic = int(table.iloc[0]["topic_id"])
            rising = (
                self.query.name(f"topic_{topic}", label_store),
                float(table.iloc[0]["change_points"]),
                window.label,
            )
        phrases = self.insight_writer.write(summary, top_theme, rising)
        return [html.Span(phrase, className="insight-item") for phrase in phrases]

    def render_time_and_sources(self, state, start_date, end_date, source_types, sources, granularity):
        key = self.current_key(state)
        article_filter = ArticleFilter.from_inputs(start_date, end_date, source_types, sources)
        rows = self.query.rows(key, self.query.filtered(article_filter))

        start, end = self.trend.window(article_filter.start_date, article_filter.end_date)
        granularity = self.trend.default_granularity(start, end) if granularity in (None, "auto") else granularity
        table, outside = self.trend.counts(rows, granularity, start, end)
        period_name = self.GRANULARITY_NAMES[granularity]
        trend_note = f"{period_name} article counts from {Formats.date(start)} to {Formats.date(end)} (UTC)."
        if outside:
            trend_note += f" Not drawn: {Formats.amount(outside, 'article')} dated outside the window."

        mix = SourceMix().table(rows)
        source_count = rows["source"].nunique()
        source_note = f"{Formats.amount(source_count, 'source')} in this view."
        if not len(rows):
            source_note = "No articles in this view."
        return TrendChart().figure(table, granularity), trend_note, SourceMixChart().figure(mix), source_note

    def render_rising(self, start_date, end_date, source_types, sources, window_key, labels):
        label_store = LabelStore(labels)
        articles = self.query.filtered(ArticleFilter.from_inputs(start_date, end_date, source_types, sources))
        window = self.rising.choose_window(articles) if window_key in (None, "auto") else self.rising.window(window_key)
        table = self.rising.compare(articles, window)
        recent_total, prior_total = table.attrs.get("recent_total", 0), table.attrs.get("prior_total", 0)
        note = (
            f"{window.label}: {Formats.count(recent_total)} recent and "
            f"{Formats.count(prior_total)} prior articles with text. "
            "Share of coverage counts unassigned articles in the base. Topics need at least "
            f"{self.rising.min_topic_articles} articles in one of the periods."
        )
        if window_key in (None, "auto") and window.key != RisingTopics.WINDOWS[0].key:
            note = "Chosen automatically because the earlier 7 day period has too few articles to compare. " + note
        if table.empty:
            return self.empty_figure("Not enough articles in both periods to compare."), note
        names = {int(topic): self.query.name(f"topic_{int(topic)}", label_store) for topic in table["topic_id"]}
        return RisingChart().figure(table, names), note

    @staticmethod
    def empty_figure(message: str) -> go.Figure:
        figure = go.Figure()
        figure.add_annotation(text=message, showarrow=False, font={"color": Theme.MUTED, "size": 13})
        figure.update_layout(**Theme.figure_layout(200))
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)
        return figure

    # Search, labels and controls

    def search_options(self, search_value, labels):
        if not search_value:
            return no_update
        results = self.search_index.search(search_value, labels)
        return [{"label": result["label"], "value": result["key"]} for result in results]

    def rename(self, apply_clicks, submits, reset_clicks, value, state, labels):
        key = self.current_key(state)
        if not self.query.tree.has(key):
            return no_update
        store = LabelStore(labels)
        if callback_context.triggered_id == Ids.RENAME_RESET:
            return store.rename(key, None)
        return store.rename(key, value)

    def export_labels(self, json_clicks, csv_clicks, labels):
        store = LabelStore(labels)
        if callback_context.triggered_id == Ids.EXPORT_JSON:
            return dcc.send_string(store.to_json(), "topic_labels.json")
        keyword_names = {key: self.query.keyword_name(key) for key in store.labels if self.query.is_known(key)}
        return dcc.send_string(store.to_csv(keyword_names), "topic_labels.csv")

    @staticmethod
    def toggle_notes(open_clicks, close_clicks):
        is_open = callback_context.triggered_id == Ids.NOTES_OPEN
        return {"display": "flex" if is_open else "none"}

    @staticmethod
    def control_graph(zoom_in, zoom_out, fit, zoom):
        trigger = callback_context.triggered_id
        zoom = zoom or 1.0
        if trigger == Ids.ZOOM_IN:
            return min(zoom * 1.25, 1.3), no_update
        if trigger == Ids.ZOOM_OUT:
            return max(zoom / 1.25, 0.25), no_update
        return no_update, {"name": "preset", "fit": True, "padding": 24 + (fit or 0) % 2}
