import pytest

from analytics.ExplorerQuery import ExplorerQuery
from components.ExplorerIds import ExplorerIds
from config.Settings import Settings
from pages.TopicExplorerPage import TopicExplorerPage
from portfolio.PortfolioApp import PortfolioApp


@pytest.fixture
def page(data_source):
    return TopicExplorerPage(data_source, Settings())


def graph_nodes(output):
    return [element["data"] for element in output[0] if "source" not in element["data"]]


def render(page, state, branches=2, labels=None):
    return page.render_view(state, None, None, [], [], branches, labels or {})


def test_app_builds_with_the_page(page):
    portfolio = PortfolioApp([page])
    assert portfolio.app.title == "Alex Geiger | Analytics Portfolio"
    assert page.layout() is not None


def test_drill_down_from_all_topics_to_a_headline(page):
    state = page.start_state()
    nodes = graph_nodes(render(page, state))
    assert nodes[0]["kind"] == "hub"
    assert {"unassigned", "missing"} <= {node["kind"] for node in nodes}

    for _ in range(6):
        branches = [node for node in nodes if node["kind"] in ("group", "topic")]
        if not branches:
            break
        state = page.next_state(ExplorerIds.GRAPH, {"data": branches[0]}, state, 2)
        nodes = graph_nodes(render(page, state))

    headlines = [node for node in nodes if node["kind"] == "headline"]
    assert headlines, "a single topic should show headline cards"
    state = page.next_state(ExplorerIds.GRAPH, {"data": headlines[0]}, state, 2)
    assert state["article"] == headlines[0]["article_id"]
    panel = render(page, state)[1]
    assert "SELECTED HEADLINE" in str(panel[0])


def test_back_home_and_breadcrumbs(page):
    state = page.next_state({"type": ExplorerIds.SUMMARY_CARD, "key": "unassigned"}, 1, page.start_state(), 2)
    assert state["path"] == [ExplorerQuery.ALL, ExplorerQuery.UNASSIGNED]
    assert page.next_state(ExplorerIds.BACK, 1, state, 2)["path"] == [ExplorerQuery.ALL]
    assert page.next_state(ExplorerIds.HOME, 1, state, 2) == page.start_state()
    deep = page.next_state(ExplorerIds.SEARCH, "topic_3", page.start_state(), 2)
    assert deep["path"][-1] == "topic_3"
    assert page.next_state({"type": ExplorerIds.CRUMB, "index": 0}, 1, deep, 2)["path"] == [ExplorerQuery.ALL]


def test_renamed_labels_show_up_in_the_view(page):
    state = page.next_state(ExplorerIds.SEARCH, "topic_4", page.start_state(), 2)
    output = render(page, state, labels={"topic_4": "Weather alerts"})
    assert output[-1] == "Weather alerts"


def test_filters_change_the_counts(page):
    everything = render(page, page.start_state())
    filtered = page.render_view(page.start_state(), None, None, ["rss"], [], 2, {})
    assert everything[3] != filtered[3]
    assert "Showing" in filtered[11]


def test_time_source_and_rising_charts_render(page):
    trend, trend_note, sources, source_note = page.render_time_and_sources(
        page.start_state(), None, None, [], [], "auto"
    )
    assert trend.data and sources.data
    assert "article counts" in trend_note
    rising, note = page.render_rising(None, None, [], [], "6h", {})
    assert "6 hours" in note
