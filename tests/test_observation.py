import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from f1_agent.evaluation.observation import build_observation
from f1_agent.track.geometry import Point2D, Route

SETTINGS = {"schema_version": 1, "lookahead_m": [5, 10], "distance_scale_m": 100, "speed_scale_mps": 40}
SQUARE = Route((Point2D(0, 0), Point2D(10, 0), Point2D(10, 10), Point2D(0, 10)), "map_metres", "observation test")


class ObservationTests(unittest.TestCase):
    def test_t4a_v1_preview_error_speed_and_validity(self):
        observation = build_observation(SQUARE, x_m=4, y_m=2, heading_rad=0, speed_mps=20,
                                        age_s=0.1, valid=True, settings=SETTINGS)
        self.assertEqual(observation["schema_version"], 1)
        self.assertEqual(observation["route_preview"], ((0.05, -0.02), (0.06, 0.02)))
        self.assertAlmostEqual(observation["lateral_error"], 0.02, delta=1e-12)
        self.assertAlmostEqual(observation["heading_error"], 0, delta=1e-12)
        self.assertAlmostEqual(observation["speed"], 0.5, delta=1e-12)
        self.assertTrue(observation["pose_valid"])
        self.assertTrue(observation["speed_valid"])
        self.assertEqual(observation["observation_age_s"], 0.1)

    def test_invalid_pose_and_speed_are_explicit_and_finite(self):
        observation = build_observation(SQUARE, x_m=None, y_m=None, heading_rad=None, speed_mps=None,
                                        age_s=0, valid=False, settings=SETTINGS)
        self.assertFalse(observation["pose_valid"])
        self.assertFalse(observation["speed_valid"])
        self.assertEqual(observation["route_preview"], ((0.0, 0.0), (0.0, 0.0)))
        self.assertTrue(all(math.isfinite(value) for value in (observation["lateral_error"], observation["heading_error"], observation["speed"])))

    def test_invalid_settings_age_and_hud_frame_reject(self):
        with self.assertRaises(ValueError):
            build_observation(SQUARE, x_m=0, y_m=0, heading_rad=0, speed_mps=0, age_s=-1, valid=True, settings=SETTINGS)
        with self.assertRaises(ValueError):
            build_observation(SQUARE, x_m=0, y_m=0, heading_rad=0, speed_mps=0, age_s=0, valid=True,
                              settings={**SETTINGS, "lookahead_m": [10, 5]})
        hud = Route(SQUARE.points, "hud_pixels", "pixel fixture")
        with self.assertRaisesRegex(ValueError, "map_metres"):
            build_observation(hud, x_m=0, y_m=0, heading_rad=0, speed_mps=0, age_s=0, valid=True, settings=SETTINGS)


if __name__ == "__main__":
    unittest.main()
