"""Schema-v1 JSON route loading and exclusive, no-overwrite saving."""
import json
import math
import os
from pathlib import Path
from .geometry import Point2D, Route

SCHEMA_VERSION = 1
_FIELDS = {"schema_version", "frame", "points", "closed", "source", "width", "width_source"}


def load_route(path: Path) -> Route:
    """Reject unknown schemas, malformed geometry and undocumented unit conversion."""
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            data = json.load(stream, parse_constant=_reject_json_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read route JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("route JSON must be an object")
    if set(data) != _FIELDS:
        missing, extra = _FIELDS - set(data), set(data) - _FIELDS
        details = []
        if missing:
            details.append("missing " + ", ".join(sorted(missing)))
        if extra:
            details.append("unknown " + ", ".join(sorted(extra)))
        raise ValueError("route JSON fields: " + "; ".join(details))
    if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported route schema_version {data['schema_version']!r}; expected {SCHEMA_VERSION}")
    if data["closed"] is not True:
        raise ValueError("schema-v1 routes must declare closed: true")
    raw_points = data["points"]
    if not isinstance(raw_points, list):
        raise ValueError("points must be an array of [x, y] coordinate pairs")
    points = []
    for index, pair in enumerate(raw_points):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"points[{index}] must be a two-number [x, y] pair")
        x, y = pair
        if not _finite(x) or not _finite(y):
            raise ValueError(f"points[{index}] coordinates must be finite numbers")
        points.append(Point2D(float(x), float(y)))
    width = data["width"]
    if width is not None:
        if not _finite(width):
            raise ValueError("width must be a finite number or null")
        width = float(width)
    return Route(tuple(points), data["frame"], data["source"], width, data["width_source"])


def save_route(route: Route, path: Path) -> None:
    """Create a new file preserving frame, point order, width and provenance."""
    if not isinstance(route, Route):
        raise TypeError("route must be a validated Route")
    data = {
        "schema_version": SCHEMA_VERSION,
        "frame": route.frame,
        "points": [[point.x, point.y] for point in route.points],
        "closed": True,
        "source": route.source,
        "width": route.width,
        "width_source": route.width_source,
    }
    # Serialize and validate before acquiring the destination path, so malformed
    # values never leave a partial file. O_EXCL protects existing user data.
    payload = (json.dumps(data, indent=2, allow_nan=False) + "\n").encode("utf-8")
    destination = Path(path)
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            destination.unlink()
        except OSError:
            pass
        raise


def _reject_json_constant(value: str):
    raise ValueError(f"non-standard JSON constant {value} is not allowed")


def _finite(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError):
        return False
