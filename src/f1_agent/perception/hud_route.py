"""T2: full HUD image to ordered route pixels; extraction is unfinished."""
from pathlib import Path
from f1_agent.track.geometry import Route


def extract_route(image_path: Path, *, crop_xywh: tuple[int, int, int, int]) -> Route:
    """Return HUD-pixel route with image/crop provenance; fail on ambiguity."""
    raise NotImplementedError("T2: implement extraction with real-image overlays")
