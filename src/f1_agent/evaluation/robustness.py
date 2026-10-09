"""T10: frozen-policy stress cases and complete-program acceptance evidence."""
from pathlib import Path

from f1_agent.training.config import ProgramConfig


def evaluate_robustness(config: ProgramConfig, checkpoint: Path, output_dir: Path) -> None:
    """Sweep declared validation scenarios; save all attempts, counts and seeds."""
    raise NotImplementedError("T10: implement robustness evaluation")
