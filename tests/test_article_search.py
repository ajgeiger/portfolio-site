from urllib.parse import unquote

from analytics.ArticleSearch import ArticleSearch
from components.CardSvg import CardSvg
from components.ExplorerIds import ExplorerIds
from components.SearchBox import SearchBox
from components.SidePanel import SidePanel
from tests.test_topic_explorer_page import render

EXAMPLES = [
    {
        "id": "a1",
        "title": "Police shootout in Lagos",
        "source": "daily.example",
        "tag": "Representative",
        "published_at": "2026-11-18T12:00:00+00:00",
    },
    {
        "id": "a2",
        "title": "Weather alerts issued",
        "source": "wire.example",
        "tag": "Sampled",
        "published_at": "2026-11-18T13:00:00+00:00",
    },
    {
        "id": "a3",
        "title": "Music festival preview",
        "source": "daily.example",
        "tag": "Sampled",
        "published_at": "2026-11-18T14:00:00+00:00",
    },
]


def test_empty_query_keeps_every_article():
    assert ArticleSearch().apply(EXAMPLES, "") == EXAMPLES
    assert ArticleSearch().apply(EXAMPLES, None) == EXAMPLES


def test_query_matches_title_source_or_tag():
    search = ArticleSearch()
    assert [row["id"] for row in search.apply(EXAMPLES, "weather")] == ["a2"]
    assert [row["id"] for row in search.apply(EXAMPLES, "DAILY")] == ["a1", "a3"]
    assert [row["id"] for row in search.apply(EXAMPLES, "representative")] == ["a1"]
    assert search.apply(EXAMPLES, "zzzz") == []


def test_filter_articles_callback_notes_the_match_count(registry, project):
    page = registry.page(project)
    rows, note = page.filter_articles(EXAMPLES, "daily")
    assert note == "2 of 3"
    assert len(rows) == 2
    empty, empty_note = page.filter_articles(EXAMPLES, "zzzz")
    assert empty_note == "No articles match"
    assert "No matching articles." in str(empty)


def test_page_layout_includes_the_article_search(registry, project):
    page = registry.page(project)
    markup = str(page.layout())
    assert ExplorerIds.ARTICLE_SEARCH in markup
    assert "search-wrap" in markup
    assert "Search articles" in markup


def test_render_view_supplies_searchable_examples(registry, project):
    page = registry.page(project)
    output = render(page, page.start_state())
    examples = output[13]
    style = output[14]
    assert examples
    assert style == {}
    assert all(isinstance(row["published_at"], str) or row["published_at"] is None for row in examples)


def test_search_box_can_be_a_text_input():
    box = SearchBox().build(ExplorerIds.ARTICLE_SEARCH, "Search articles", kind="input")
    assert box.className == "search-wrap"
    assert box.children[1].id == ExplorerIds.ARTICLE_SEARCH
    assert box.children[1].className == "search-input"


def test_branch_card_accent_is_clipped_and_inset():
    svg = CardSvg.branch("3 TOPICS", "Sample", "10 articles", 0.4, "group")
    raw = unquote(svg.split(",", 1)[1])
    assert 'clipPath id="card"' in raw
    assert 'clip-path="url(#card)"' in raw
    assert f'x="{CardSvg.ACCENT_X}"' in raw
    assert f'rx="{CardSvg.ACCENT_WIDTH / 2}"' in raw
    assert f'height="{CardSvg.BAR_HEIGHT}" rx="{CardSvg.BAR_HEIGHT / 2}"' in raw
    assert 'x="1" y="1" width="6"' not in raw


def test_side_panel_section_uses_the_search_box():
    section = SidePanel.article_section()
    assert section.id == ExplorerIds.ARTICLE_SECTION
    assert "search-wrap" in str(section)
