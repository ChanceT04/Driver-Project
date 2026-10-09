"""Shared JSON config envelope; each feature owner validates its own settings.

Only schema version, required sections and experiment bookkeeping are validated
here today. A successful load does not imply runnable physics or learning.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .experiment import ExperimentConfig


@dataclass(frozen=True)
class ProgramConfig:
    source: Path
    settings: dict[str, Any]

    def experiment(self, output_dir: Path) -> ExperimentConfig:
        """Convert shared run settings to the existing runner contract."""
        section = self.settings["experiment"]
        return ExperimentConfig(
            output_dir=output_dir,
            train_routes=tuple(section["train_routes"]),
            validation_routes=tuple(section["validation_routes"]),
            test_routes=tuple(section["test_routes"]),
            train_episodes=section["train_episodes"],
            max_steps=section["max_steps"],
            validate_every=section["validate_every"],
            episode_seed=section["episode_seed"],
            evaluation_repeats=section["evaluation_repeats"],
        )


def load_config(path: Path) -> ProgramConfig:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON value: {value}")

    settings = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    sections = {"experiment", "track", "vehicle", "observation", "reward", "agent", "randomization"}
    if not isinstance(settings, dict) or type(settings.get("schema_version")) is not int or settings["schema_version"] != 1:
        raise ValueError("config must be an object with schema_version 1")
    if set(settings) != sections | {"schema_version"}:
        raise ValueError("config sections must be: schema_version, " + ", ".join(sorted(sections)))
    for name in sections:
        if not isinstance(settings[name], dict):
            raise ValueError(f"config section {name} must be an object")
    experiment = settings["experiment"]
    fields = {"train_routes", "validation_routes", "test_routes", "train_episodes",
              "max_steps", "validate_every", "episode_seed", "evaluation_repeats"}
    if set(experiment) != fields:
        raise ValueError("experiment fields must be: " + ", ".join(sorted(fields)))
    for name in ("train_routes", "validation_routes", "test_routes"):
        seeds = experiment[name]
        if not isinstance(seeds, list) or not seeds or any(type(seed) is not int or seed < 0 for seed in seeds):
            raise ValueError(f"{name} must be a nonempty array of nonnegative integer seeds")
    for name in fields - {"train_routes", "validation_routes", "test_routes"}:
        value = experiment[name]
        minimum = 0 if name == "episode_seed" else 1
        if type(value) is not int or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    config = ProgramConfig(path.resolve(), settings)
    config.experiment(Path("unused-config-validation"))  # validates split separation; no I/O
    return config
