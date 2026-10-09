"""T6: compact learned driver; select algorithm after simulator measurements."""
from __future__ import annotations
from pathlib import Path
from f1_agent.training.config import ProgramConfig
from f1_agent.training.interfaces import Action, Observation, Transition


class LearningAgent:
    """Feed-forward first policy implementing TrainableAgent."""
    def __init__(self, config: ProgramConfig) -> None:
        raise NotImplementedError("T6: select and implement a learning agent")

    def act(self, observation: Observation, *, explore: bool) -> Action:
        raise NotImplementedError("T6: implement policy inference")

    def observe(self, transition: Transition) -> None:
        raise NotImplementedError("T6: implement learning updates or rollout collection")

    def end_episode(self) -> None:
        raise NotImplementedError("T6: implement episode-end learning hook")

    def save(self, path: Path) -> None:
        """Save weights, architecture, normalization, schema and training metadata."""
        raise NotImplementedError("T6: implement checkpoint writing")

    @classmethod
    def load(cls, path: Path) -> LearningAgent:
        """Reconstruct preprocessing and policy without relying on mutable defaults."""
        raise NotImplementedError("T6: implement checkpoint loading")
