"""T5: scoring from private simulator state, never a policy input."""
from __future__ import annotations

from typing import Mapping


def driving_reward(
    *, forward_progress_m: float, elapsed_s: float, departed: bool,
    lap_complete: bool, weights: Mapping[str, float],
) -> float:
    """Use newly earned progress, not repeated finish-line crossings.

    The environment owns progress unwrapping, continuity and traversal checks.
    T4A may return zero reward until T5 implements and verifies this function.
    """
    raise NotImplementedError("T5: implement and probe driving reward")
