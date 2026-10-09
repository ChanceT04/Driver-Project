"""Contract tests for the training runner, independent of car physics."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from f1_agent.training.experiment import ExperimentConfig, run_episode, run_experiment
from f1_agent.training.interfaces import Action, StepResult, Transition


class ToyEnvironment:
    """A two-step episode used only to exercise the framework."""

    def reset(self, *, route_seed: int, episode_seed: int) -> dict[str, object]:
        self.route_seed = route_seed
        self.episode_seed = episode_seed
        self.progress = 0
        return {"progress": self.progress}

    def step(self, action: Action) -> StepResult:
        self.progress += int(action.throttle > 0)
        complete = self.progress >= 2
        return StepResult(
            observation={"progress": self.progress},
            reward=float(self.progress),
            terminated=complete,
            truncated=False,
            metrics={"progress_m": float(self.progress), "lap_complete": complete},
        )


class ToyAgent:
    def __init__(self) -> None:
        self.exploration_flags: list[bool] = []
        self.transitions = 0
        self.ended_episodes = 0
        self.last_transition: Transition | None = None

    def act(self, observation: object, *, explore: bool) -> Action:
        self.exploration_flags.append(explore)
        return Action(steer=0.0, throttle=1.0, brake=0.0)

    def observe(self, transition: Transition) -> None:
        self.transitions += 1
        self.last_transition = transition

    def end_episode(self) -> None:
        self.ended_episodes += 1

    def save(self, path: Path) -> None:
        path.with_suffix(".json").write_text(
            json.dumps({"transitions": self.transitions}), encoding="utf-8"
        )


class TrainingFrameworkTests(unittest.TestCase):
    def test_action_limits_and_reward_finiteness(self) -> None:
        with self.assertRaises(ValueError):
            Action(steer=1.1, throttle=0.0, brake=0.0)
        with self.assertRaises(ValueError):
            Action(steer=0.0, throttle=float("nan"), brake=0.0)
        with self.assertRaises(ValueError):
            StepResult({}, float("inf"), False, False)

    def test_route_splits_must_be_disjoint(self) -> None:
        with self.assertRaises(ValueError):
            ExperimentConfig(Path("unused"), (1, 2), (2,), (3,), 2, 3, 1)

    def test_step_limit_truncates_without_claiming_lap_completion(self) -> None:
        summary = run_episode(
            ToyEnvironment(), ToyAgent(), split="validation", route_seed=4,
            episode_seed=10, max_steps=1, training=False,
        )
        self.assertTrue(summary.truncated)
        self.assertFalse(summary.terminated)
        self.assertFalse(summary.lap_complete)
        self.assertEqual(summary.steps, 1)

    def test_learning_transition_hides_privileged_metrics(self) -> None:
        agent = ToyAgent()
        run_episode(
            ToyEnvironment(), agent, split="train", route_seed=4,
            episode_seed=10, max_steps=1, training=True,
        )
        self.assertIsNotNone(agent.last_transition)
        self.assertTrue(agent.last_transition.truncated)
        self.assertFalse(hasattr(agent.last_transition, "metrics"))

    def test_experiment_isolated_splits_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            output = Path(temporary) / "run"
            config = ExperimentConfig(
                output_dir=output, train_routes=(11, 12),
                validation_routes=(21,), test_routes=(31,),
                train_episodes=4, max_steps=3, validate_every=2,
                episode_seed=7,
            )
            agent = ToyAgent()
            summaries = run_experiment(config, ToyEnvironment, agent)
            self.assertEqual([s.split for s in summaries].count("train"), 4)
            self.assertEqual([s.split for s in summaries].count("validation"), 3)
            self.assertEqual([s.split for s in summaries].count("test"), 1)
            self.assertEqual({s.route_seed for s in summaries if s.split == "train"}, {11, 12})
            self.assertEqual({s.route_seed for s in summaries if s.split == "validation"}, {21})
            self.assertEqual({s.route_seed for s in summaries if s.split == "test"}, {31})
            self.assertEqual(
                [s.episode_seed for s in summaries if s.split == "validation"],
                [2_000_007, 2_000_007, 2_000_007],
            )
            self.assertEqual(
                [s.training_episode for s in summaries if s.split == "validation"],
                [0, 2, 4],
            )
            self.assertEqual(agent.transitions, 8)
            self.assertEqual(agent.ended_episodes, 4)
            self.assertEqual(agent.exploration_flags.count(True), 8)
            self.assertEqual(agent.exploration_flags.count(False), 8)
            self.assertTrue((output / "config.json").exists())
            self.assertEqual(len((output / "episodes.jsonl").read_text().splitlines()), 8)
            self.assertTrue((output / "checkpoints" / "episode-0.json").exists())
            self.assertTrue((output / "checkpoints" / "episode-2.json").exists())
            self.assertTrue((output / "checkpoints" / "episode-4.json").exists())
            self.assertEqual(json.loads((output / "policy.json").read_text()), {"transitions": 8})
            with self.assertRaises(FileExistsError):
                run_experiment(config, ToyEnvironment, ToyAgent())

    def test_final_episode_gets_validation_even_before_interval(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            config = ExperimentConfig(
                Path(temporary) / "run", (1,), (2,), (3,),
                train_episodes=1, max_steps=3, validate_every=10,
            )
            summaries = run_experiment(config, ToyEnvironment, ToyAgent())
            self.assertEqual(
                [item.split for item in summaries],
                ["validation", "train", "validation", "test"],
            )


if __name__ == "__main__":
    unittest.main()
