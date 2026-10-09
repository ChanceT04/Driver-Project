"""T4A introduces, T5 finalizes common observations; T8 produces them live.

Version 1: local route preview (forward, left), lateral error (+left), heading
error (route minus car, CCW), speed, validity and age. See docs/architecture.md.
Exclude track identity, absolute coordinates and synthetic road boundaries.
"""
from __future__ import annotations
import math
from typing import Mapping
from f1_agent.track.geometry import Point2D, Route
from f1_agent.training.interfaces import Observation


def build_observation(
    route: Route, *, x_m: float | None, y_m: float | None,
    heading_rad: float | None, speed_mps: float | None,
    age_s: float, valid: bool, settings: Mapping[str, object],
) -> Observation:
    """Require a metre route; flag invalid/missing inputs explicitly."""
    if route.frame != "map_metres":
        raise ValueError("driving observations require a map_metres route")
    if not isinstance(settings, Mapping):
        raise ValueError("observation settings must be a mapping")
    allowed = {"schema_version", "lookahead_m", "distance_scale_m", "speed_scale_mps"}
    if set(settings) != allowed:
        raise ValueError("observation settings must contain schema_version, lookahead_m, distance_scale_m, speed_scale_mps")
    if type(settings["schema_version"]) is not int or settings["schema_version"] != 1:
        raise ValueError("observation schema_version must be 1")
    lookahead = settings["lookahead_m"]
    if not isinstance(lookahead, (list, tuple)) or not lookahead or any(not _finite(value) or value <= 0 for value in lookahead):
        raise ValueError("lookahead_m must be a nonempty sequence of positive finite distances")
    if any(right <= left for left, right in zip(lookahead, lookahead[1:])):
        raise ValueError("lookahead_m values must be strictly increasing")
    distance_scale = settings["distance_scale_m"]
    speed_scale = settings["speed_scale_mps"]
    if not _finite(distance_scale) or distance_scale <= 0 or not _finite(speed_scale) or speed_scale <= 0:
        raise ValueError("observation scales must be finite and positive")
    if not _finite(age_s) or age_s < 0:
        raise ValueError("age_s must be finite and nonnegative")
    if type(valid) is not bool:
        raise ValueError("valid must be a boolean")

    pose_valid = valid and all(_finite(value) for value in (x_m, y_m, heading_rad))
    speed_valid = _finite(speed_mps) and speed_mps >= 0
    if pose_valid:
        projection = route.project(Point2D(float(x_m), float(y_m)))
        heading = float(heading_rad)
        previews = []
        for distance in lookahead:
            point = route.sample(projection.distance_along + float(distance))
            dx, dy = point.x - float(x_m), point.y - float(y_m)
            forward = math.cos(heading) * dx + math.sin(heading) * dy
            left = -math.sin(heading) * dx + math.cos(heading) * dy
            previews.append((forward / float(distance_scale), left / float(distance_scale)))
        lateral = projection.lateral_offset / float(distance_scale)
        heading_error = math.atan2(math.sin(projection.tangent_rad - heading), math.cos(projection.tangent_rad - heading)) / math.pi
    else:
        previews = [(0.0, 0.0) for _ in lookahead]
        lateral = 0.0
        heading_error = 0.0
    speed = float(speed_mps) / float(speed_scale) if speed_valid else 0.0
    return {
        "schema_version": 1,
        "route_preview": tuple(previews),
        "lateral_error": lateral,
        "heading_error": heading_error,
        "speed": speed,
        "pose_valid": pose_valid,
        "speed_valid": speed_valid,
        "observation_age_s": float(age_s),
    }


def _finite(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError):
        return False
