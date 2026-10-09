"""Closed-route geometry shared by imported and generated tracks.

map_metres uses x right, y up; hud_pixels uses x right, y down. Points follow
travel direction. Distances use the route frame's units. Lateral offset is
positive LEFT of travel in both frames (account for the HUD y-axis flip).
"""
from __future__ import annotations
from dataclasses import dataclass
import bisect
import math
from typing import Literal

CoordinateFrame = Literal["map_metres", "hud_pixels"]


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True)
class Projection:
    point: Point2D
    distance_along: float
    lateral_offset: float
    tangent_rad: float


@dataclass(frozen=True)
class Route:
    points: tuple[Point2D, ...]
    frame: CoordinateFrame
    source: str
    width: float | None = None
    width_source: Literal["synthetic", "measured", "estimated", "unavailable"] = "unavailable"

    def __post_init__(self) -> None:
        if self.frame not in ("map_metres", "hud_pixels"):
            raise ValueError("frame must be 'map_metres' or 'hud_pixels'")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string")
        if self.width_source not in ("synthetic", "measured", "estimated", "unavailable"):
            raise ValueError("width_source must be synthetic, measured, estimated, or unavailable")
        if self.width is None:
            if self.width_source != "unavailable":
                raise ValueError("width_source requires a width; use 'unavailable' when width is missing")
        elif not _finite(self.width) or self.width <= 0:
            raise ValueError("width must be finite and positive")
        elif self.width_source == "unavailable":
            raise ValueError("width_source 'unavailable' contradicts a supplied width")
        if not isinstance(self.points, tuple):
            raise ValueError("points must be an ordered tuple of Point2D values")
        points = self.points
        if len(points) >= 2 and points[-1] == points[0]:
            points = points[:-1]
            object.__setattr__(self, "points", points)
        if len(points) < 3:
            raise ValueError("a closed route needs at least three distinct points")
        for point in points:
            if not isinstance(point, Point2D) or not _finite(point.x) or not _finite(point.y):
                raise ValueError("route coordinates must be finite Point2D values")
        edges = tuple(math.hypot(b.x - a.x, b.y - a.y) for a, b in zip(points, points[1:] + points[:1]))
        if any(edge == 0 for edge in edges):
            raise ValueError("route contains a zero-length segment")
        if not math.isfinite(sum(edges)) or sum(edges) <= 0:
            raise ValueError("route must have finite positive length")
        twice_area = sum(a.x * b.y - b.x * a.y for a, b in zip(points, points[1:] + points[:1]))
        if not math.isfinite(twice_area) or twice_area == 0:
            raise ValueError("route geometry must enclose non-zero area")

    @property
    def length(self) -> float:
        return sum(math.hypot(b.x - a.x, b.y - a.y) for a, b in zip(self.points, self.points[1:] + self.points[:1]))

    def sample(self, distance_along: float) -> Point2D:
        """Sample wrapped arc length; accept distances spanning either loop end."""
        distance = _route_distance(distance_along, self.length)
        edges, cumulative = self._edges_and_cumulative()
        index = min(bisect.bisect_right(cumulative, distance) - 1, len(edges) - 1)
        fraction = (distance - cumulative[index]) / edges[index]
        start, end = self.points[index], self.points[(index + 1) % len(self.points)]
        return Point2D(start.x + fraction * (end.x - start.x), start.y + fraction * (end.y - start.y))

    def tangent(self, distance_along: float) -> float:
        """Angle atan2(dy, dx) in this frame; visual sense differs for HUD pixels."""
        distance = _route_distance(distance_along, self.length)
        edges, cumulative = self._edges_and_cumulative()
        index = min(bisect.bisect_right(cumulative, distance) - 1, len(edges) - 1)
        start, end = self.points[index], self.points[(index + 1) % len(self.points)]
        return math.atan2(end.y - start.y, end.x - start.x)

    def project(self, point: Point2D, *, near_distance: float | None = None) -> Projection:
        """Use prior progress when needed to disambiguate nearby branches."""
        if not isinstance(point, Point2D) or not _finite(point.x) or not _finite(point.y):
            raise ValueError("projection point must have finite coordinates")
        length = self.length
        hint = None if near_distance is None else _route_distance(near_distance, length)
        edges, cumulative = self._edges_and_cumulative()
        candidates = []
        for index, edge in enumerate(edges):
            start, end = self.points[index], self.points[(index + 1) % len(self.points)]
            dx, dy = end.x - start.x, end.y - start.y
            fraction = max(0.0, min(1.0, ((point.x - start.x) * dx + (point.y - start.y) * dy) / (edge * edge)))
            projected = Point2D(start.x + fraction * dx, start.y + fraction * dy)
            along = (cumulative[index] + fraction * edge) % length
            dist_sq = (point.x - projected.x) ** 2 + (point.y - projected.y) ** 2
            candidates.append((dist_sq, along, index, projected, dx / edge, dy / edge))
        minimum = min(candidate[0] for candidate in candidates)
        # Exact geometric ties prefer the candidate closest in wrapped progress to
        # the hint; without a hint, the lowest segment index wins.
        tied = [candidate for candidate in candidates if candidate[0] == minimum]
        if hint is None:
            chosen = min(tied, key=lambda candidate: candidate[2])
        else:
            chosen = min(tied, key=lambda candidate: (_wrapped_delta(candidate[1], hint, length), candidate[2]))
        _, along, _, projected, tx, ty = chosen
        cross = tx * (point.y - projected.y) - ty * (point.x - projected.x)
        lateral = cross if self.frame == "map_metres" else -cross
        return Projection(projected, along, lateral, math.atan2(ty, tx))

    def _edges_and_cumulative(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        edges = tuple(math.hypot(b.x - a.x, b.y - a.y) for a, b in zip(self.points, self.points[1:] + self.points[:1]))
        cumulative = [0.0]
        for edge in edges:
            cumulative.append(cumulative[-1] + edge)
        return edges, tuple(cumulative)


def _finite(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError):
        return False


def _route_distance(value: float, length: float) -> float:
    if not _finite(value):
        raise ValueError("distance must be finite")
    return float(value) % length


def _wrapped_delta(a: float, b: float, length: float) -> float:
    delta = abs(a - b) % length
    return min(delta, length - delta)
