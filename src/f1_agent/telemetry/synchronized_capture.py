"""T7: independent screen/UDP capture on one local monotonic clock."""
from pathlib import Path
from typing import Mapping


def capture_session(output_dir: Path, settings: Mapping[str, object]) -> None:
    """Create replayable frames, raw UDP and timing/drop metadata in a new directory."""
    raise NotImplementedError("T7: implement synchronized read-only capture")
