import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from f1_agent.track.geometry import Point2D, Route


def square(frame="map_metres", points=None):
    points = points or (Point2D(0, 0), Point2D(10, 0), Point2D(10, 10), Point2D(0, 10))
    return Route(points, frame, "hand-calculated test square")


class TrackGeometryTests(unittest.TestCase):
    def test_t1_01_square_length_and_wrapped_samples(self):
        route = square()
        self.assertAlmostEqual(route.length, 40.0, delta=1e-8)
        for distance, expected in ((5, (5, 0)), (15, (10, 5)), (40, (0, 0)), (45, (5, 0)), (-5, (0, 5))):
            with self.subTest(distance=distance):
                point = route.sample(distance)
                self.assertAlmostEqual(point.x, expected[0], delta=1e-8)
                self.assertAlmostEqual(point.y, expected[1], delta=1e-8)

    def test_t1_02_projection_and_left_offset(self):
        projected = square().project(Point2D(4, 2))
        self.assertAlmostEqual(projected.point.x, 4, delta=1e-8)
        self.assertAlmostEqual(projected.point.y, 0, delta=1e-8)
        self.assertAlmostEqual(projected.distance_along, 4, delta=1e-8)
        self.assertAlmostEqual(projected.lateral_offset, 2, delta=1e-8)
        self.assertAlmostEqual(projected.tangent_rad, 0, delta=1e-8)

    def test_t1_03_reverse_direction_and_hud_sign(self):
        reverse = square(points=(Point2D(0, 0), Point2D(0, 10), Point2D(10, 10), Point2D(10, 0)))
        projected = reverse.project(Point2D(4, 2))
        self.assertAlmostEqual(projected.point.x, 4, delta=1e-8)
        self.assertAlmostEqual(projected.point.y, 0, delta=1e-8)
        self.assertAlmostEqual(projected.distance_along, 36, delta=1e-8)
        self.assertAlmostEqual(projected.lateral_offset, -2, delta=1e-8)
        self.assertAlmostEqual(math.remainder(projected.tangent_rad - math.pi, 2 * math.pi), 0, delta=1e-8)
        hud = square(frame="hud_pixels").project(Point2D(4, 2))
        self.assertAlmostEqual(hud.lateral_offset, -2, delta=1e-8)

    def test_t1_04_duplicate_endpoint_vertex_and_progress_hint(self):
        canonical = square()
        repeated = square(points=canonical.points + (canonical.points[0],))
        self.assertEqual(repeated.points, canonical.points)
        self.assertEqual(repeated.length, canonical.length)
        for distance in (-5, 0, 5, 10, 25, 40, 45):
            self.assertEqual(repeated.sample(distance), canonical.sample(distance))
        vertex = canonical.project(Point2D(10, 0))
        self.assertEqual(vertex.point, Point2D(10, 0))
        self.assertEqual(vertex.distance_along, 10)
        self.assertEqual(vertex.tangent_rad, 0)  # exact tie: lowest segment index

        near = Route((Point2D(0, 0), Point2D(10, 0), Point2D(10, 2), Point2D(0, 2), Point2D(0, 1)), "map_metres", "nearby branches")
        no_hint = near.project(Point2D(5, 1))
        with_hint = near.project(Point2D(5, 1), near_distance=18)
        self.assertEqual(no_hint.distance_along, 5)
        self.assertEqual(with_hint.distance_along, 17)
        self.assertEqual(with_hint.point, Point2D(5, 2))

    def test_t1_05_invalid_route_geometry_and_metadata(self):
        valid = (Point2D(0, 0), Point2D(1, 0), Point2D(0, 1))
        invalid_routes = (
            ((), "map_metres", "source"),
            ((Point2D(0, 0), Point2D(1, 0)), "map_metres", "source"),
            ((Point2D(0, 0), Point2D(1, 0), Point2D(2, 0)), "map_metres", "source"),
            ((Point2D(0, 0), Point2D(1, 0), Point2D(float("nan"), 1)), "map_metres", "source"),
            (valid, "unknown", "source"),
        )
        for points, frame, source in invalid_routes:
            with self.subTest(points=points, frame=frame):
                with self.assertRaises(ValueError):
                    Route(points, frame, source)
        for kwargs in (
            {"width": 0, "width_source": "synthetic"},
            {"width": -2, "width_source": "measured"},
            {"width": None, "width_source": "estimated"},
            {"width": 4, "width_source": "unavailable"},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    Route(valid, "map_metres", "source", **kwargs)
        with self.assertRaises(ValueError):
            square().sample(float("inf"))


if __name__ == "__main__":
    unittest.main()
