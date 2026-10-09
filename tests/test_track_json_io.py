import json
import tempfile
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from f1_agent.track.geometry import Point2D, Route
from f1_agent.track.json_io import load_route, save_route

ROOT = Path(__file__).resolve().parents[1]
OVAL = ROOT / "tests" / "fixtures" / "tracks" / "oval.json"


class TrackJsonTests(unittest.TestCase):
    def test_t1_05_reject_unsupported_version_and_malformed_metadata(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "bad.json"
            data = json.loads(OVAL.read_text(encoding="utf-8"))
            data["schema_version"] = 2
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported route schema_version"):
                load_route(path)
            data = json.loads(OVAL.read_text(encoding="utf-8"))
            data["width"] = None
            data["width_source"] = "synthetic"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "width_source requires a width"):
                load_route(path)

    def test_t1_06_square_and_oval_round_trip_and_no_overwrite(self):
        square = Route((Point2D(0, 0), Point2D(10, 0), Point2D(10, 10), Point2D(0, 10)), "map_metres", "test square", 6.0, "measured")
        oval = load_route(OVAL)
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            for name, route in (("square.json", square), ("oval.json", oval)):
                path = Path(directory) / name
                save_route(route, path)
                loaded = load_route(path)
                self.assertEqual(loaded, route)
                self.assertEqual(loaded.frame, route.frame)
                self.assertEqual(loaded.points, route.points)
                self.assertEqual(loaded.width_source, route.width_source)
            sentinel = Path(directory) / "sentinel.json"
            sentinel.write_bytes(b"do not replace\x00")
            with self.assertRaises(FileExistsError):
                save_route(square, sentinel)
            self.assertEqual(sentinel.read_bytes(), b"do not replace\x00")

    def test_t1_05_reject_unclosed_and_nonfinite_json(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "bad.json"
            data = json.loads(OVAL.read_text(encoding="utf-8"))
            data["closed"] = False
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "closed: true"):
                load_route(path)
            path.write_text('{"schema_version":1,"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-standard JSON constant"):
                load_route(path)


if __name__ == "__main__":
    unittest.main()
