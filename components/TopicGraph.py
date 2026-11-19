"""Lay out the hub and its branches for the center graph."""

import dash_cytoscape as cytoscape

from components.BezierPath import BezierPath
from components.CardSvg import CardSvg
from config.Theme import Theme


class TopicGraph:
    """Build the graph component and its elements.

    The hub sits in the middle. Branches alternate between a left and a right
    column, largest first, and connect to the hub with horizontal S curves.
    The positions and curves are for reading only. They do not encode
    similarity or importance.
    """

    COLUMN_GAP = 330
    ROW_GAP = 124

    STYLESHEET = [
        {
            "selector": "node",
            "style": {
                "shape": "round-rectangle",
                "width": "data(width)",
                "height": "data(height)",
                "background-image": "data(image)",
                "background-fit": "contain",
                "background-opacity": 0,
                "border-width": 0,
                "label": "",
            },
        },
        {"selector": "node.hub", "style": {"shape": "ellipse"}},
        {"selector": "node:active", "style": {"overlay-opacity": 0.06, "overlay-color": Theme.ACCENT}},
        {
            "selector": "edge",
            "style": {
                "curve-style": "unbundled-bezier",
                "control-point-distances": "data(bend)",
                "control-point-weights": "data(weights)",
                "source-endpoint": "data(source_endpoint)",
                "target-endpoint": "data(target_endpoint)",
                "edge-distances": "endpoints",
                "line-color": "#B8C2D3",
                "width": 1.6,
                "opacity": 0.9,
            },
        },
    ]

    def component(self, component_id: str):
        return cytoscape.Cytoscape(
            id=component_id,
            elements=[],
            layout={"name": "preset", "fit": True, "padding": 24},
            stylesheet=self.STYLESHEET,
            minZoom=0.25,
            maxZoom=1.3,
            wheelSensitivity=0.2,
            boxSelectionEnabled=False,
            autounselectify=True,
            responsive=True,
            style={"width": "100%", "height": "580px"},
        )

    def elements(self, hub: dict, branches: list[dict]) -> list[dict]:
        """Return Cytoscape elements.

        Args:
            hub: {"key", "image"} for the center circle.
            branches: [{"key", "image", "width", "height", "kind"}], largest first.
                Any extra keys, such as article_id, are kept on the node data.
        """
        size = CardSvg.HUB_SIZE
        elements = [
            {
                "data": {"id": hub["key"], "image": hub["image"], "width": size, "height": size, "kind": "hub"},
                "position": {"x": 0, "y": 0},
                "classes": "hub",
                "grabbable": True,
            }
        ]
        left = branches[0::2]
        right = branches[1::2]
        for side, column in ((-1, left), (1, right)):
            top = -(len(column) - 1) * self.ROW_GAP / 2
            for row, branch in enumerate(column):
                x = side * (self.COLUMN_GAP + branch["width"] / 2 - CardSvg.BRANCH_SIZE[0] / 2)
                y = top + row * self.ROW_GAP
                node_id = f"node::{branch['key']}"
                elements.append(
                    {
                        "data": {"id": node_id, **branch},
                        "position": {"x": x, "y": y},
                    }
                )
                elements.append(self.edge(hub["key"], node_id, branch["key"], side, size, x, y, branch["width"]))
        return elements

    @staticmethod
    def edge(
        hub_key: str,
        node_id: str,
        branch_key: str,
        side: int,
        hub_size: float,
        x: float,
        y: float,
        width: float,
    ) -> dict:
        """An S-shaped link from the side of the hub to the inner side of a card."""
        source_endpoint = "50% 0%" if side == 1 else "-50% 0%"
        target_endpoint = "-50% 0%" if side == 1 else "50% 0%"
        curve = BezierPath.horizontal(side * hub_size / 2, 0.0, x - side * width / 2, y)
        weights, distances = curve.cytoscape_controls()
        return {
            "data": {
                "id": f"edge::{branch_key}",
                "source": hub_key,
                "target": node_id,
                "path": curve.svg,
                "weights": weights,
                "bend": distances,
                "source_endpoint": source_endpoint,
                "target_endpoint": target_endpoint,
            }
        }
