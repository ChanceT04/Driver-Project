"""T4A/T5: diagnostic drivers for checking the simulator and learning results."""
from __future__ import annotations

import math

from f1_agent.training.interfaces import Action, Observation


class ZeroActionPolicy:
    def act(self, observation: Observation, *, explore: bool = False) -> Action:
        return Action(steer=0.0, throttle=0.0, brake=0.0)


class RouteFollower:
    """Uses only the same route preview and speed available to a learned policy."""

    def __init__(self, *, wheelbase_m: float = 3.6, max_steering_rad: float = 0.35,
                 speed_scale_mps: float = 40.0, target_speed_mps: float = 5.0,
                 distance_scale_m: float = 100.0) -> None:
        if any(not math.isfinite(value) or value <= 0 for value in
               (wheelbase_m, max_steering_rad, speed_scale_mps, target_speed_mps, distance_scale_m)):
            raise ValueError("follower parameters must be finite and positive")
        self.wheelbase_m = wheelbase_m
        self.max_steering_rad = max_steering_rad
        self.speed_scale_mps = speed_scale_mps
        self.target_speed_mps = target_speed_mps
        self.distance_scale_m = distance_scale_m

    def act(self, observation: Observation, *, explore: bool = False) -> Action:
        if observation.get("pose_valid") is not True:
            return Action(0.0, 0.0, 1.0)
        previews = observation.get("route_preview")
        if not isinstance(previews, (tuple, list)) or not previews:
            raise ValueError("observation route_preview must be a nonempty sequence")
        # The 10 m preview is the main pure-pursuit target; normalized distance
        # cancels in alpha and curvature, so no absolute route coordinates leak in.
        target = previews[min(1, len(previews) - 1)]
        if not isinstance(target, (tuple, list)) or len(target) != 2:
            raise ValueError("each route preview must be a (forward, left) pair")
        forward, left = target
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in (forward, left)):
            raise ValueError("route preview values must be finite")
        distance = math.hypot(forward, left) * self.distance_scale_m
        alpha = math.atan2(left, forward)
        # Pure-pursuit curvature, expressed as the bicycle steering angle. The
        # action sign is inverted because positive Action.steer means right.
        curvature = 0.0 if distance < 1e-8 else 2.0 * math.sin(alpha) / distance
        steering_angle = math.atan(self.wheelbase_m * curvature)
        steer = max(-1.0, min(1.0, -steering_angle / self.max_steering_rad))
        speed_value = observation.get("speed", 0.0)
        if observation.get("speed_valid") is not True or not isinstance(speed_value, (int, float)) or not math.isfinite(speed_value):
            return Action(steer, 0.0, 0.5)
        speed = max(0.0, float(speed_value) * self.speed_scale_mps)
        curvature_speed = self.target_speed_mps if abs(curvature) < 1e-6 else min(
            self.target_speed_mps, math.sqrt(5.0 / abs(curvature))
        )
        if speed < curvature_speed - 0.4:
            throttle = max(0.15, min(1.0, (curvature_speed - speed) / 2.5))
            brake = 0.0
        elif speed > curvature_speed + 0.35:
            throttle = 0.0
            brake = min(1.0, (speed - curvature_speed) / 2.0)
        else:
            throttle, brake = 0.2, 0.0
        return Action(steer, throttle, brake)
