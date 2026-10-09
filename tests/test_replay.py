import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from f1_agent.environment.render import replay_episode

CONFIG = ROOT / "configs" / "offline.example.json"
ROUTE = ROOT / "tests" / "fixtures" / "tracks" / "oval.json"


class ReplayTests(unittest.TestCase):
    def test_t4a_07_saved_replay_is_physics_independent_and_rejects_bad_inputs(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            temp = Path(directory)
            run = temp / "run"
            command = [sys.executable, str(ROOT / "scripts" / "sim.py"), "simulate", "--config", str(CONFIG),
                       "--route", str(ROUTE), "--output", str(run)]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            episode = run / "episode.jsonl"
            outcomes = json.loads((run / "summary.json").read_text(encoding="utf-8"))["outcomes"]
            self.assertTrue(outcomes["follower"]["lap_complete"])
            self.assertFalse(outcomes["zero_action"]["lap_complete"])
            self.assertEqual(outcomes["zero_action"]["failure_reason"], "stalled")
            self.assertFalse(outcomes["departure"]["lap_complete"])
            self.assertEqual(outcomes["departure"]["failure_reason"], "departure")
            html_path = temp / "replay.html"
            with patch("f1_agent.environment.simulator.advance", side_effect=AssertionError("physics must not run during replay")):
                replay_episode(episode, html_path)
            rendered = html_path.read_text(encoding="utf-8")
            self.assertIn("<canvas", rendered)
            self.assertIn("Recorded drive replay", rendered)
            self.assertIn('"lap_complete":true', rendered)

            lines = episode.read_text(encoding="utf-8").splitlines()
            bad_version = temp / "version.jsonl"
            metadata = json.loads(lines[0])
            metadata["schema_version"] = 2
            bad_version.write_text("\n".join([json.dumps(metadata), *lines[1:]]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported or missing replay metadata"):
                replay_episode(bad_version, temp / "bad.html")
            self.assertFalse((temp / "bad.html").exists())

            empty = temp / "empty.jsonl"
            empty.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "empty or truncated"):
                replay_episode(empty, temp / "empty.html")
            truncated = temp / "truncated.jsonl"
            truncated.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "final outcome record"):
                replay_episode(truncated, temp / "truncated.html")

            sentinel = temp / "sentinel.html"
            sentinel.write_bytes(b"existing page")
            with self.assertRaises(FileExistsError):
                replay_episode(episode, sentinel)
            self.assertEqual(sentinel.read_bytes(), b"existing page")


if __name__ == "__main__":
    unittest.main()
