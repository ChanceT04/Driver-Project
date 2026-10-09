"""Small contracts shared by the future simulator and learning algorithm.

These contracts do not implement car physics or a policy. T4A/T4B supply an
environment, T5 defines observation fields and metrics, and T6 supplies an
agent. Keeping the runner dependent on protocols lets those tickets evolve.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
from typing import Mapping, Protocol


Observation = Mapping[str, object]
Metric = float | int | bool


@dataclass(frozen=True)
class Action:
    """Normalized car commands; steering is negative left, positive right."""

    steer: float
    throttle: float
    brake: float

    def __post_init__(self) -> None:
        for name, value, minimum, maximum in (
            ("steer", self.steer, -1.0, 1.0),
            ("throttle", self.throttle, 0.0, 1.0),
            ("brake", self.brake, 0.0, 1.0),
        ):
            if not math.isfinite(value) or not minimum <= value <= maximum:
                raise ValueError(f"{name} must be finite and in [{minimum}, {maximum}]")


@dataclass(frozen=True)
class StepResult:
    """One environment step, with scoring data kept out of observations."""

    observation: Observation
    reward: float
    terminated: bool
    truncated: bool
    metrics: Mapping[str, Metric] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not math.isfinite(self.reward):
            raise ValueError("reward must be finite")


@dataclass(frozen=True)
class Transition:
    """Learning data only; privileged evaluation metrics are deliberately absent."""

    observation: Observation
    action: Action
    next_observation: Observation
    reward: float
    terminated: bool
    truncated: bool


class DrivingEnvironment(Protocol):
    """T4A/T4B implement this interface; reset starts a fresh episode."""

    def reset(self, *, route_seed: int, episode_seed: int) -> Observation: ...

    def step(self, action: Action) -> StepResult: ...


class TrainableAgent(Protocol):
    """T6 implements this interface; evaluation never calls learning hooks."""

    def act(self, observation: Observation, *, explore: bool) -> Action: ...

    def observe(self, transition: Transition) -> None: ...

    def end_episode(self) -> None: ...

    def save(self, path: Path) -> None: ...
