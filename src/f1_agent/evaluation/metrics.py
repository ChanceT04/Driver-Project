"""T5/T6: baseline and frozen-policy evaluation on whole unseen routes."""
from __future__ import annotations
from pathlib import Path
from typing import Sequence
from f1_agent.training.config import ProgramConfig
from f1_agent.training.experiment import EpisodeSummary


def summarize_episodes(episodes: Sequence[EpisodeSummary]) -> dict[str, object]:
    """Completion counts/rates, failure distance, valid-lap time and smoothness."""
    raise NotImplementedError("T5: implement driving metrics")


def evaluate(
    config: ProgramConfig, output_dir: Path, *, checkpoint: Path | None = None,
    split: str = "validation",
) -> None:
    """T5 compares baselines; T6 loads frozen policies. Evaluation never learns."""
    raise NotImplementedError("T5/T6: implement evaluation command")
