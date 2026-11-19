import math

from components.BezierPath import BezierPath
from components.ExplorerIds import ExplorerIds
from components.SearchBox import SearchBox
from components.TopicGraph import TopicGraph
from tests.test_topic_explorer_page import render


def apply_cytoscape(curve: BezierPath, weight: float, distance: float) -> tuple[float, float]:
    """Place a control point the way Cytoscape unbundled-bezier does."""
    dx = curve.x1 - curve.x0
    dy = curve.y1 - curve.y0
    length = math.hypot(dx, dy)
    mid_x = (1 - weight) * curve.x0 + weight * curve.x1
    mid_y = (1 - weight) * curve.y0 + weight * curve.y1
    return mid_x + (-dy / length) * distance, mid_y + (dx / length) * distance


def test_svg_path_is_a_horizontal_s_curve():
    curve = BezierPath.horizontal(0, 0, 100, 40)
    assert curve.svg == "M 0.0,0.0 C 50.0,0.0 50.0,40.0 100.0,40.0"
    assert curve.control_points == ((50.0, 0.0), (50.0, 40.0))


def test_level_points_make_a_straight_line():
    curve = BezierPath.horizontal(10, 5, 90, 5)
    assert curve.svg == "M 10.0,5.0 C 50.0,5.0 50.0,5.0 90.0,5.0"
    weights, distances = curve.cytoscape_controls()
    assert weights == "0.5000 0.5000"
    assert distances == "0.00 0.00"


def test_cytoscape_controls_are_close_to_the_bezier_handles():
    curve = BezierPath.horizontal(105, 0, 250, 124)
    weights, distances = curve.cytoscape_controls()
    w1, w2 = (float(value) for value in weights.split())
    d1, d2 = (float(value) for value in distances.split())
    first = apply_cytoscape(curve, w1, d1)
    second = apply_cytoscape(curve, w2, d2)
    for got, expected in ((first, curve.control_points[0]), (second, curve.control_points[1])):
        assert math.isclose(got[0], expected[0], abs_tol=0.05)
        assert math.isclose(got[1], expected[1], abs_tol=0.05)


def test_graph_edges_carry_an_s_path(registry, project):
    page = registry.page(project)
    view = render(page, page.start_state())[0]
    edges = [element["data"] for element in view if "source" in element["data"]]
    assert edges
    for edge in edges:
        assert edge["path"].startswith("M ")
        assert " C " in edge["path"]
        assert len(edge["weights"].split()) == 2
        assert len(edge["bend"].split()) == 2
        assert edge["source_endpoint"].endswith("0%")
        assert edge["target_endpoint"].endswith("0%")


def test_topic_graph_stylesheet_uses_endpoint_beziers():
    style = next(rule["style"] for rule in TopicGraph.STYLESHEET if rule["selector"] == "edge")
    assert style["curve-style"] == "unbundled-bezier"
    assert style["edge-distances"] == "endpoints"
    assert style["control-point-weights"] == "data(weights)"


def test_search_box_is_a_rounded_wrapper():
    box = SearchBox().build(ExplorerIds.SEARCH, "Search topics")
    assert box.className == "search-wrap"
    assert box.children[0].className == "search-icon"
    dropdown = box.children[1]
    assert dropdown.id == ExplorerIds.SEARCH
    assert dropdown.className == "search"
