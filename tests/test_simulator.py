import copy
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from f1_agent.environment.dynamics import VehicleState, advance
from f1_agent.environment.simulator import DrivingSimulator
from f1_agent.policy.baselines import RouteFollower, ZeroActionPolicy
from f1_agent.track.json_io import load_route
from f1_agent.training.config import ProgramConfig, load_config
from f1_agent.training.interfaces import Action

CONFIG_PATH = ROOT / "configs" / "offline.example.json"
ROUTE_PATH = ROOT / "tests" / "fixtures" / "tracks" / "oval.json"


def physics(**overrides):
    values = {
        "time_step_s": 0.1,
        "wheelbase_m": 3.6,
        "max_steering_rad": 0.35,
        "max_acceleration_mps2": 0.0,
        "max_braking_mps2": 0.0,
        "max_speed_mps": 100.0,
        "drag_coefficient_per_m": 0.0,
    }
    values.update(overrides)
    return values


def config(*, max_steps=None, vehicle_changes=None):
    base = load_config(CONFIG_PATH)
    settings = copy.deepcopy(base.settings)
    settings["experiment"]["max_steps"] = max_steps or settings["experiment"]["max_steps"]
    if vehicle_changes:
        settings["vehicle"].update(vehicle_changes)
    return ProgramConfig(base.source, settings)


class SimulatorTests(unittest.TestCase):
    def test_t4a_01_straight_motion_and_heading(self):
        p = physics()
        for heading, expected in ((0.0, (1.0, 0.0)), (math.pi / 2, (0.0, 1.0))):
            result = advance(VehicleState(0, 0, heading, 10), Action(0, 0, 0), p)
            self.assertAlmostEqual(result.x_m, expected[0], delta=1e-8)
            self.assertAlmostEqual(result.y_m, expected[1], delta=1e-8)
            self.assertAlmostEqual(result.speed_mps, 10, delta=1e-8)
            self.assertAlmostEqual(result.heading_rad, heading, delta=1e-8)

    def test_t4a_02_acceleration_and_braking(self):
        accelerating = VehicleState(0, 0, 0, 0)
        for _ in range(10):
            accelerating = advance(accelerating, Action(0, 1, 0), physics(max_acceleration_mps2=2))
        self.assertAlmostEqual(accelerating.speed_mps, 2, delta=1e-8)
        braking = advance(VehicleState(0, 0, 0, 1), Action(0, 0, 1), physics(time_step_s=1, max_braking_mps2=5))
        self.assertEqual(braking.speed_mps, 0)

    def test_t4a_03_steering_sign_and_mirror_symmetry(self):
        p = physics()
        left = advance(VehicleState(0, 0, 0, 10), Action(-0.5, 0, 0), p)
        right = advance(VehicleState(0, 0, 0, 10), Action(0.5, 0, 0), p)
        self.assertGreater(left.heading_rad, 0)
        self.assertLess(right.heading_rad, 0)
        self.assertAlmostEqual(left.x_m, right.x_m, delta=1e-6)
        self.assertAlmostEqual(left.y_m, -right.y_m, delta=1e-6)

    def test_t4a_04_reset_replay_and_invalid_physics(self):
        route = load_route(ROUTE_PATH)
        fixed_route = type(route)(route.points, route.frame, route.source, 10000.0, "synthetic")
        base = config(max_steps=500)
        first = DrivingSimulator(base, lambda _seed: fixed_route)
        second = DrivingSimulator(base, lambda _seed: fixed_route)
        first.reset(route_seed=12, episode_seed=33)
        second.reset(route_seed=12, episode_seed=33)
        actions = [Action(0, 0.2, 0) for _ in range(200)]
        for action in actions:
            a = first.step(action)
            b = second.step(action)
            self.assertEqual(first.snapshot(), second.snapshot())
            self.assertEqual((a.reward, a.terminated, a.truncated), (b.reward, b.terminated, b.truncated))
            if a.terminated or a.truncated:
                self.fail("the deterministic replay should remain active for 200 actions")

        first.reset(route_seed=7, episode_seed=9)
        second.reset(route_seed=7, episode_seed=9)
        self.assertEqual(first.snapshot(), second.snapshot())
        finished = DrivingSimulator(base, lambda _seed: route)
        finished.reset(route_seed=2, episode_seed=3)
        for _ in range(120):
            result = finished.step(Action(0, 0, 0))
            if result.terminated:
                break
        self.assertTrue(result.terminated)
        reset_state = finished.reset(route_seed=2, episode_seed=3)
        fresh = DrivingSimulator(base, lambda _seed: route)
        fresh_state = fresh.reset(route_seed=2, episode_seed=3)
        self.assertEqual(finished.snapshot(), fresh.snapshot())
        self.assertEqual(reset_state, fresh_state)
        for bad in (physics(time_step_s=0), physics(time_step_s=-0.1), physics(max_acceleration_mps2=float("inf")),
                    physics(max_steering_rad=math.pi / 2)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                advance(VehicleState(0, 0, 0, 1), Action(0, 0, 0), bad)
        with self.assertRaises(ValueError):
            DrivingSimulator(config(vehicle_changes={"time_step_s": 0}), lambda _seed: route)

    def test_t4a_05_spawn_stall_departure_limit_and_end_guard(self):
        route = load_route(ROUTE_PATH)
        stationary = DrivingSimulator(config(), lambda _seed: route)
        stationary.reset(route_seed=0, episode_seed=0)
        for _ in range(20):
            result = stationary.step(Action(0, 0, 0))
            self.assertFalse(result.metrics["lap_complete"])
        for _ in range(100):
            result = stationary.step(Action(0, 0, 0))
            if result.terminated:
                break
        self.assertTrue(result.terminated)
        self.assertEqual(result.metrics["failure_reason"], "stalled")
        self.assertFalse(result.metrics["lap_complete"])
        with self.assertRaises(RuntimeError):
            stationary.step(Action(0, 0, 0))

        narrow_route = type(route)(route.points, route.frame, route.source, 0.1, "synthetic")
        departing = DrivingSimulator(config(), lambda _seed: narrow_route)
        departing.reset(route_seed=0, episode_seed=0)
        departing.state = VehicleState(0, 0, 0, 5)
        for _ in range(20):
            result = departing.step(Action(-1, 0, 0))
            if result.terminated:
                break
        self.assertTrue(result.terminated)
        self.assertEqual(result.metrics["failure_reason"], "departure")

        limited = DrivingSimulator(config(max_steps=1), lambda _seed: route)
        limited.reset(route_seed=0, episode_seed=0)
        result = limited.step(Action(0, 0, 0))
        self.assertFalse(result.terminated)
        self.assertTrue(result.truncated)
        self.assertFalse(result.metrics["lap_complete"])

    def test_t4a_06_follower_completes_zero_action_does_not(self):
        route = load_route(ROUTE_PATH)
        settings = config()
        vehicle = settings.settings["vehicle"]
        observation = settings.settings["observation"]
        follower = RouteFollower(
            wheelbase_m=vehicle["wheelbase_m"], max_steering_rad=vehicle["max_steering_rad"],
            speed_scale_mps=observation["speed_scale_mps"], target_speed_mps=5,
            distance_scale_m=observation["distance_scale_m"],
        )
        for policy, should_finish in ((follower, True), (ZeroActionPolicy(), False)):
            simulator = DrivingSimulator(settings, lambda _seed: route)
            current = simulator.reset(route_seed=0, episode_seed=0)
            result = None
            progress_wrapped = False
            previous_route_progress = 0.0
            while True:
                result = simulator.step(policy.act(current))
                current = result.observation
                route_progress = result.metrics["route_progress_m"]
                if previous_route_progress > route.length * 0.9 and route_progress < route.length * 0.1:
                    progress_wrapped = True
                previous_route_progress = route_progress
                if result.terminated or result.truncated:
                    break
            self.assertEqual(result.metrics["lap_complete"], should_finish)
            if should_finish:
                self.assertTrue(result.terminated)
                self.assertFalse(result.truncated)
                self.assertTrue(progress_wrapped, "the follower should cross the route finish line during its lap")
            else:
                self.assertEqual(result.metrics["failure_reason"], "stalled")


if __name__ == "__main__":
    unittest.main()
