"""T6: assemble geometry, simulator and learning around the existing runner."""
from pathlib import Path
from .config import ProgramConfig


def train(config: ProgramConfig, output_dir: Path) -> None:
    """Validate settings, seed learning, persist resolved config and run experiment.

    Own algorithm setup, checkpoint selection/reload and training curves.
    Adapt the runner for validation-only development runs; reserve final test
    evaluation for a declared frozen candidate.
    """
    raise NotImplementedError("T6: implement complete training command")
