"""Build a horizontal S curve between two points."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BezierPath:
    """A cubic Bezier that leaves and arrives horizontally.

    The path is M x0,y0 C xm,y0 xm,y1 x1,y1, where xm is the midpoint of
    x0 and x1. That makes a smooth S, or a straight line when the points
    share a y value.
    """

    x0: float
    y0: float
    x1: float
    y1: float

    @classmethod
    def horizontal(cls, x0: float, y0: float, x1: float, y1: float) -> BezierPath:
        return cls(x0, y0, x1, y1)

    @property
    def mid_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def svg(self) -> str:
        mid = self.mid_x
        return (
            f"M {self.x0:.1f},{self.y0:.1f} "
            f"C {mid:.1f},{self.y0:.1f} {mid:.1f},{self.y1:.1f} {self.x1:.1f},{self.y1:.1f}"
        )

    @property
    def control_points(self) -> tuple[tuple[float, float], tuple[float, float]]:
        mid = self.mid_x
        return (mid, self.y0), (mid, self.y1)

    def cytoscape_controls(self) -> tuple[str, str]:
        """Weights and perpendicular distances for an unbundled bezier.

        Cytoscape places each control point at a weighted spot along the
        source to target line, then offsets it by a distance along the
        left-hand normal (-dy, dx). These values recreate the horizontal
        S so the graph can keep using Cytoscape for hover and click.
        """
        dx = self.x1 - self.x0
        dy = self.y1 - self.y0
        length = math.hypot(dx, dy)
        if length == 0:
            return "0.5 0.5", "0 0"
        weight = (dx * dx) / (2 * length * length)
        distance = (dx * dy) / (2 * length)
        return f"{weight:.4f} {1 - weight:.4f}", f"{self.format_distance(-distance)} {self.format_distance(distance)}"

    @staticmethod
    def format_distance(value: float) -> str:
        """Avoid a signed zero in the Cytoscape distance string."""
        return f"{(0.0 if abs(value) < 0.005 else value):.2f}"
