"""T3: reproducible varied routes. Seeds identify entire layouts."""
from pathlib import Path
from typing import Mapping
from f1_agent.training.config import ProgramConfig
from .geometry import Route


def generate_route(seed: int, settings: Mapping[str, object]) -> Route:
    """Generate map metres with synthetic width; bound retries on invalid loops."""
    raise NotImplementedError("T3: implement procedural routes")


def preview_tracks(config: ProgramConfig, output_dir: Path) -> None:
    """Render split-labelled layouts and generator rejection statistics."""
    raise NotImplementedError("T3: implement track preview command")
