"""Check configuration isolation and honest failure at unfinished entry points.

These checks validate the scaffold, not driving or learning behavior.
"""
from __future__ import annotations

import json
import io
import os
from contextlib import redirect_stderr
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from f1_agent.training.config import load_config
from f1_agent.cli import main


class ProgramScaffoldTests(unittest.TestCase):
    def test_example_maps_to_runner_without_creating_output(self) -> None:
        config = load_config(PROJECT_ROOT / "configs/offline.example.json")
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as directory:
            output = Path(directory) / "run"
            experiment = config.experiment(output)
            self.assertFalse(output.exists())
            self.assertTrue(set(experiment.train_routes).isdisjoint(experiment.test_routes))
            self.assertIsNone(config.settings["agent"]["method"])

    def test_invalid_shared_configs_are_rejected(self) -> None:
        example = json.loads((PROJECT_ROOT / "configs/offline.example.json").read_text())
        cases = []
        overlap = json.loads(json.dumps(example))
        overlap["experiment"]["test_routes"] = overlap["experiment"]["train_routes"]
        cases.append(overlap)
        typo = json.loads(json.dumps(example))
        typo["experiments"] = typo.pop("experiment")
        cases.append(typo)
        wrong_type = json.loads(json.dumps(example))
        wrong_type["experiment"]["train_episodes"] = True
        cases.append(wrong_type)
        unknown_version = json.loads(json.dumps(example))
        unknown_version["schema_version"] = 2
        cases.append(unknown_version)
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as directory:
            path = Path(directory) / "config.json"
            for value in cases:
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_config(path)

    def test_commands_fail_clearly_without_creating_fake_runs(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as directory:
            for command, target in (
                ("preview-tracks", "f1_agent.track.procedural.preview_tracks"),
                ("simulate", "f1_agent.environment.demo.simulate"),
                ("train", "f1_agent.training.sim_train.train"),
                ("evaluate", "f1_agent.evaluation.metrics.evaluate"),
            ):
                with self.subTest(command=command):
                    output = Path(directory) / command
                    stderr = io.StringIO()
                    # Inject a feature failure so this test still applies once implemented.
                    with patch(target, side_effect=NotImplementedError("feature unavailable")):
                        with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
                            main([command, "--config", str(PROJECT_ROOT / "configs/offline.example.json"),
                                  "--output", str(output)])
                    self.assertEqual(error.exception.code, 1)
                    self.assertIn("feature unavailable", stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())
                    self.assertFalse(output.exists())

    def test_source_entry_point_help_and_config_check(self) -> None:
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for arguments in (["--help"], ["check-config", "--config", "configs/offline.example.json"]):
            result = subprocess.run(
                [sys.executable, "scripts/sim.py", *arguments], cwd=PROJECT_ROOT,
                capture_output=True, text=True, env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
