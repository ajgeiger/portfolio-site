"""The 'How to read this' window with method notes and limits."""

from dash import html

from components.ExplorerIds import ExplorerIds
from config.Formats import Formats


class MethodNotesModal:
    """Explain how the numbers are made and where they fall short."""

    def build(self, metadata: dict) -> html.Div:
        repeat_share = metadata["repeat_text_rows"] / max(metadata["rows_with_text"], 1)
        earliest = Formats.date(metadata["earliest_published"])
        load_time = Formats.date_time(metadata["last_load_time"])
        clusters = Formats.count(metadata.get("hdbscan_clusters", 0))
        kept = Formats.count(metadata.get("clusters_kept_as_topics", metadata["topic_count"]))
        sections = [
            (
                "Reading the graph",
                [
                    "The circle in the middle is the current view. It starts at All topics, which holds every article.",
                    "Each card around it is one branch of the current view: a group of similar topics (shown as N "
                    "TOPICS) "
                    "or a single topic (shown as TOPIC n). The bar on a card is its share of the current view.",
                    "Click a card to go one level down. At a single topic the cards become example headlines, and "
                    "clicking "
                    "one shows its full title, summary, source, date and a link.",
                    "Card positions and the curved lines are for reading only. They do not measure similarity or "
                    "importance. "
                    "Cards alternate left and right from largest to smallest.",
                ],
            ),
            (
                "Counting",
                [
                    "Counts are article rows, not unique stories. A syndicated story counts once for every outlet "
                    "that ran it. "
                    f"In this data {Formats.count(metadata['repeat_text_rows'])} rows "
                    f"({Formats.percent(repeat_share)}) repeat "
                    "a headline that already appears elsewhere.",
                    "Topic, group and Unassigned percentages use every article with text as the base, Unassigned "
                    "included. "
                    "The Missing percentage uses every row as the base.",
                    "The side panel also shows each view's share of the group you came from.",
                    "Unassigned (topic -1) holds stories the model could not place with enough confidence: one off "
                    "items "
                    "and vague headlines. Missing text (topic -2) holds rows with a blank headline. The two are "
                    "never mixed.",
                ],
            ),
            (
                "Labels",
                [
                    "Labels are keyword based until renamed. Each topic is named from its top c-TF-IDF keywords; "
                    "each group "
                    "combines the keywords of its topics, weighted by article count, so larger topics drive the name.",
                    "Some topics form around publisher boilerplate rather than a story, for example a site name or a "
                    "wire "
                    "service tagline repeated in every headline. Treat those as source clusters, and rename them if "
                    "useful.",
                    "Renamed labels apply to the current session only. Export them as JSON (topic id to label, ready "
                    "for "
                    "TopicModel.set_topic_labels) or CSV (every renamed topic and group) to carry them into the next "
                    "run.",
                ],
            ),
            (
                "How topics are grouped",
                [
                    "Topics come from the Headline Radar model: MiniLM sentence embeddings, UMAP, HDBSCAN and "
                    "c-TF-IDF keywords. "
                    "This app only reads the fitted results. Nothing is fit or retrained here.",
                    f"HDBSCAN found {clusters} clusters. After identical headlines voted on a shared cluster and "
                    f"small clusters were dropped, {kept} were kept as topics.",
                    "The tree is built from each topic's c-TF-IDF keyword profile, projected onto 30 latent themes, "
                    "scaled to unit length (so distance follows cosine similarity) and merged step by step with "
                    "Ward linkage.",
                    "Each view opens the largest remaining group until it shows the chosen number of branches.",
                    "Example headlines tagged Representative were chosen by the model as closest to the topic's "
                    "keywords. "
                    "Headlines tagged Sampled are a fixed random sample of the current selection.",
                ],
            ),
            (
                "Time and dates",
                [
                    f"Times are in UTC. The last data load was {load_time}. The trend chart ends at that load and "
                    "starts where 99% of articles begin, at most 7 days back, unless a date filter is set. It "
                    "reports how "
                    "many articles fall outside the window.",
                    "Rising topics compare each topic's share of coverage in a recent window with the window just "
                    "before it. "
                    "The default is 7 days; when the earlier period has too few articles, it falls back to 24 hours "
                    "and then 6 hours.",
                    f"Some publish dates cannot be right. {Formats.count(metadata['stale_date_rows'])} articles are "
                    "dated more than "
                    f"{metadata['stale_after_days']} days before the load (the earliest is {earliest}), usually old "
                    "pages a feed "
                    f"picked up again, and {Formats.count(metadata['future_date_rows'])} are dated after the load. "
                    "They are kept "
                    "in every count and only matter for the time charts.",
                ],
            ),
        ]
        body = [
            html.Div([html.H4(title), html.Ul([html.Li(item) for item in items])], className="notes-section")
            for title, items in sections
        ]
        return html.Div(
            html.Div(
                [
                    html.Div(
                        [
                            html.H3("How to read this"),
                            html.Button("Close", id=ExplorerIds.NOTES_CLOSE, className="nav-button", n_clicks=0),
                        ],
                        className="modal-header",
                    ),
                    html.Div(body, className="modal-body"),
                ],
                className="modal-card",
                role="dialog",
            ),
            id=ExplorerIds.NOTES_MODAL,
            className="modal-backdrop",
            style={"display": "none"},
        )
