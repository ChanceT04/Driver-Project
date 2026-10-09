"""T2: player triangle detection. The circle in the old clip is the ghost."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MarkerDetection:
    timestamp_ns: int
    x_px: float | None
    y_px: float | None
    heading_rad: float | None
    confidence: float
    # Heading is atan2(dy, dx) in HUD pixels (y down); T8 converts to map axes.


def detect_player(
    image_path: Path, *, crop_xywh: tuple[int, int, int, int], timestamp_ns: int,
) -> MarkerDetection:
    """Missing detection returns null pose; never recycle an old location silently."""
    raise NotImplementedError("T2: implement player triangle and heading detection")
