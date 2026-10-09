"""Reproducible episode orchestration, split discipline, and run artifacts.

This is training infrastructure, not a trainer or a driving policy. T4A/T4B and T6
provide the environment and agent that make a real experiment possible.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
from typing import Callable, Iterable

from .interfaces import DrivingEnvironment, TrainableAgent, Transition


@dataclass(frozen=True)
class ExperimentConfig:
    output_dir: Path
    train_routes: tuple[int, ...]
    validation_routes: tuple[int, ...]
    test_routes: tuple[int, ...]
    train_episodes: int
    max_steps: int
    validate_every: int
    episode_seed: int = 0
    evaluation_repeats: int = 1

    def __post_init__(self) -> None:
        groups = (self.train_routes, self.validation_routes, self.test_routes)
        if any(not group or len(group) != len(set(group)) for group in groups):
            raise ValueError("each route split must be nonempty and contain unique seeds")
        if sum(map(len, groups)) != len(set().union(*map(set, groups))):
            raise ValueError("train, validation, and test route seeds must be disjoint")
        if min(self.train_episodes, self.max_steps, self.validate_every, self.evaluation_repeats) <= 0:
            raise ValueError("episode and evaluation counts must be positive")


@dataclass(frozen=True)
class EpisodeSummary:
    split: str
    training_episode: int
    route_seed: int
    episode_seed: int
    steps: int
    total_reward: float
    terminated: bool
    truncated: bool
    lap_complete: bool
    progress_m: float | None
    final_metrics: dict[str, float | int | bool]


def run_episode(
    environment: DrivingEnvironment,
    agent: TrainableAgent,
    *,
    split: str,
    route_seed: int,
    episode_seed: int,
    max_steps: int,
    training: bool,
    training_episode: int = 0,
) -> EpisodeSummary:
    """Run one episode; only training episodes update the agent."""
    if max_steps <= 0:
        raise ValueError("max_steps must be positive")
    observation = environment.reset(route_seed=route_seed, episode_seed=episode_seed)
    total_reward = 0.0
    for step_index in range(1, max_steps + 1):
        action = agent.act(observation, explore=training)
        result = environment.step(action)
        total_reward += result.reward
        if training:
            agent.observe(Transition(
                observation=observation, action=action,
                next_observation=result.observation, reward=result.reward,
                terminated=result.terminated,
                truncated=result.truncated or (step_index == max_steps and not result.terminated),
            ))
        observation = result.observation
        if result.terminated or result.truncated or step_index == max_steps:
            metrics = dict(result.metrics)
            progress = metrics.get("progress_m")
            summary = EpisodeSummary(
                split=split,
                training_episode=training_episode,
                route_seed=route_seed,
                episode_seed=episode_seed,
                steps=step_index,
                total_reward=total_reward,
                terminated=result.terminated,
                truncated=result.truncated or (step_index == max_steps and not result.terminated),
                lap_complete=metrics.get("lap_complete") is True,
                progress_m=float(progress) if progress is not None else None,
                final_metrics=metrics,
            )
            if training:
                agent.end_episode()
            return summary
    raise AssertionError("positive max_steps must end the episode")


def _evaluate(
    make_environment: Callable[[], DrivingEnvironment],
    agent: TrainableAgent,
    *,
    split: str,
    training_episode: int,
    routes: Iterable[int],
    repeats: int,
    episode_seed: int,
    max_steps: int,
) -> list[EpisodeSummary]:
    return [
        run_episode(
            make_environment(), agent, split=split,
            training_episode=training_episode, route_seed=route_seed,
            episode_seed=episode_seed + route_index * repeats + repeat,
            max_steps=max_steps, training=False,
        )
        for route_index, route_seed in enumerate(routes)
        for repeat in range(repeats)
    ]


def _write_summary(stream, summary: EpisodeSummary) -> None:
    stream.write(json.dumps(asdict(summary), allow_nan=False, separators=(",", ":")) + "\n")


def run_experiment(
    config: ExperimentConfig,
    make_environment: Callable[[], DrivingEnvironment],
    agent: TrainableAgent,
) -> list[EpisodeSummary]:
    """Train, validate periodically, test once at the end, and save a policy.

    The run directory must not already exist. The agent owns the format of its
    saved policy; the runner records config and per-episode JSONL beside it.
    Validation always uses fixed episode seeds for fair checkpoint comparison.
    """
    config.output_dir.mkdir(parents=True, exist_ok=False)
    metadata = asdict(config)
    metadata["output_dir"] = str(config.output_dir)
    metadata["framework_schema_version"] = 1
    (config.output_dir / "config.json").write_text(
        json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    rng = random.Random(config.episode_seed)
    route_order: list[int] = []
    summaries: list[EpisodeSummary] = []
    checkpoints = config.output_dir / "checkpoints"
    checkpoints.mkdir()
    with (config.output_dir / "episodes.jsonl").open("x", encoding="utf-8") as log:
        initial = _evaluate(
            make_environment, agent, split="validation", training_episode=0,
            routes=config.validation_routes, repeats=config.evaluation_repeats,
            episode_seed=config.episode_seed + 2_000_000,
            max_steps=config.max_steps,
        )
        summaries.extend(initial)
        for result in initial:
            _write_summary(log, result)
        agent.save(checkpoints / "episode-0")
        for episode_index in range(config.train_episodes):
            if not route_order:
                route_order = list(config.train_routes)
                rng.shuffle(route_order)
            route_seed = route_order.pop()
            summary = run_episode(
                make_environment(), agent, split="train",
                training_episode=episode_index + 1, route_seed=route_seed,
                episode_seed=config.episode_seed + 1_000_000 + episode_index,
                max_steps=config.max_steps, training=True,
            )
            summaries.append(summary)
            _write_summary(log, summary)
            if (episode_index + 1) % config.validate_every == 0 or episode_index + 1 == config.train_episodes:
                validation = _evaluate(
                    make_environment, agent, split="validation",
                    training_episode=episode_index + 1,
                    routes=config.validation_routes, repeats=config.evaluation_repeats,
                    episode_seed=config.episode_seed + 2_000_000,
                    max_steps=config.max_steps,
                )
                summaries.extend(validation)
                for result in validation:
                    _write_summary(log, result)
                agent.save(checkpoints / f"episode-{episode_index + 1}")
        test = _evaluate(
            make_environment, agent, split="test",
            training_episode=config.train_episodes, routes=config.test_routes,
            repeats=config.evaluation_repeats,
            episode_seed=config.episode_seed + 3_000_000,
            max_steps=config.max_steps,
        )
        summaries.extend(test)
        for result in test:
            _write_summary(log, result)
    agent.save(config.output_dir / "policy")
    return summaries
