"""T4A/T4B: deterministic car environment, then generated-route support."""
from __future__ import annotations
import math
from typing import Callable, Mapping
from f1_agent.environment.dynamics import VehicleState, advance
from f1_agent.evaluation.observation import build_observation
from f1_agent.track.geometry import Point2D, Route
from f1_agent.training.config import ProgramConfig
from f1_agent.training.interfaces import Action, Observation, StepResult

_VEHICLE_FIELDS = {
    "time_step_s", "wheelbase_m", "max_steering_rad", "steering_response_s",
    "max_acceleration_mps2", "max_braking_mps2", "max_speed_mps",
    "drag_coefficient_per_m", "max_lateral_acceleration_mps2", "command_delay_s",
}
_OBSERVATION_FIELDS = {"schema_version", "lookahead_m", "speed_scale_mps", "distance_scale_m"}


class DrivingSimulator:
    """Implements DrivingEnvironment; route injection keeps T4A independent of T3."""
    def __init__(self, config: ProgramConfig, route_provider: Callable[[int], Route]) -> None:
        if not callable(route_provider):
            raise TypeError("route_provider must be callable")
        settings = config.settings
        vehicle = settings.get("vehicle")
        observation = settings.get("observation")
        experiment = settings.get("experiment")
        if not isinstance(vehicle, Mapping) or set(vehicle) != _VEHICLE_FIELDS:
            raise ValueError("vehicle settings must contain the supported offline vehicle fields")
        if not isinstance(observation, Mapping) or set(observation) != _OBSERVATION_FIELDS:
            raise ValueError("observation settings must contain schema-v1 preview and scale fields")
        if not isinstance(experiment, Mapping) or type(experiment.get("max_steps")) is not int or experiment["max_steps"] <= 0:
            raise ValueError("experiment.max_steps must be a positive integer")
        self._validate_vehicle(vehicle)
        self._validate_observation(observation)
        self.config = config
        self._vehicle = dict(vehicle)
        self._observation_settings = dict(observation)
        self._max_steps = experiment["max_steps"]
        self._route_provider = route_provider
        self.route: Route | None = None
        self.state: VehicleState | None = None
        self._step_count = 0
        self._elapsed_s = 0.0
        self._last_progress = 0.0
        self._unwrapped_progress = 0.0
        self._distance_travelled = 0.0
        self._stalled_s = 0.0
        self._ended = False
        self._terminated = False
        self._truncated = False
        self._lap_complete = False
        self._failure_reason: str | None = None
        self._route_seed = 0
        self._episode_seed = 0

    @staticmethod
    def _validate_vehicle(vehicle: Mapping[str, object]) -> None:
        for key in _VEHICLE_FIELDS:
            value = vehicle[key]
            if not _finite(value):
                raise ValueError(f"vehicle.{key} must be finite")
        if vehicle["time_step_s"] <= 0 or vehicle["wheelbase_m"] <= 0 or vehicle["max_speed_mps"] <= 0:
            raise ValueError("vehicle time_step_s, wheelbase_m and max_speed_mps must be positive")
        if vehicle["max_steering_rad"] >= math.pi / 2:
            raise ValueError("vehicle.max_steering_rad must be less than pi/2")
        for key in ("max_steering_rad", "steering_response_s", "max_acceleration_mps2",
                    "max_braking_mps2", "drag_coefficient_per_m", "max_lateral_acceleration_mps2",
                    "command_delay_s"):
            if vehicle[key] < 0:
                raise ValueError(f"vehicle.{key} must be nonnegative")
        if vehicle["max_steering_rad"] <= 0:
            raise ValueError("vehicle.max_steering_rad must be positive for the T4A follower")

    @staticmethod
    def _validate_observation(settings: Mapping[str, object]) -> None:
        if type(settings["schema_version"]) is not int or settings["schema_version"] != 1:
            raise ValueError("observation.schema_version must be 1")
        lookahead = settings["lookahead_m"]
        if not isinstance(lookahead, (list, tuple)) or not lookahead or any(not _finite(value) or value <= 0 for value in lookahead):
            raise ValueError("observation.lookahead_m must contain positive finite distances")
        if any(right <= left for left, right in zip(lookahead, lookahead[1:])):
            raise ValueError("observation.lookahead_m must be strictly increasing")
        for key in ("speed_scale_mps", "distance_scale_m"):
            if not _finite(settings[key]) or settings[key] <= 0:
                raise ValueError(f"observation.{key} must be finite and positive")

    def reset(self, *, route_seed: int, episode_seed: int) -> Observation:
        """Seed starts separately from route identity; clear delay/progress history."""
        route = self._route_provider(route_seed)
        if not isinstance(route, Route) or route.frame != "map_metres":
            raise ValueError("T4A simulator route provider must return a map_metres Route")
        if route.width is None:
            raise ValueError("T4A departure checks require a route width")
        self.route = route
        self._route_seed = route_seed
        self._episode_seed = episode_seed
        start = route.sample(0.0)
        self.state = VehicleState(start.x, start.y, route.tangent(0.0), 0.0)
        self._step_count = 0
        self._elapsed_s = 0.0
        self._last_progress = 0.0
        self._unwrapped_progress = 0.0
        self._distance_travelled = 0.0
        self._stalled_s = 0.0
        self._ended = False
        self._terminated = False
        self._truncated = False
        self._lap_complete = False
        self._failure_reason = None
        return self._observation()

    def step(self, action: Action) -> StepResult:
        """Advance fixed dt; return policy observation and separate private metrics."""
        if self.route is None or self.state is None:
            raise RuntimeError("reset must be called before step")
        if self._ended:
            raise RuntimeError("episode has ended; call reset before stepping again")
        dt = float(self._vehicle["time_step_s"])
        old_state = self.state
        self.state = advance(old_state, action, self._vehicle)
        self._step_count += 1
        self._elapsed_s += dt
        moved = math.hypot(self.state.x_m - old_state.x_m, self.state.y_m - old_state.y_m)
        self._distance_travelled += moved
        projection = self.route.project(Point2D(self.state.x_m, self.state.y_m), near_distance=self._last_progress)
        delta = (projection.distance_along - self._last_progress + self.route.length / 2) % self.route.length - self.route.length / 2
        # Reject apparent progress jumps that exceed plausible motion; this keeps
        # nearby branches and finish-line projection from manufacturing a lap.
        if abs(delta) > moved * 1.25 + 0.05:
            delta = 0.0
        self._unwrapped_progress += delta
        self._last_progress = projection.distance_along
        if delta <= 0.01:
            self._stalled_s += dt
        else:
            self._stalled_s = 0.0

        if abs(projection.lateral_offset) > self.route.width / 2:
            self._failure_reason = "departure"
        elif self._stalled_s >= 5.0:
            self._failure_reason = "stalled"
        elif self._unwrapped_progress >= self.route.length - 0.05:
            self._lap_complete = True
        terminated = self._failure_reason is not None or self._lap_complete
        truncated = not terminated and self._step_count >= self._max_steps
        self._ended = terminated or truncated
        self._terminated = terminated
        self._truncated = truncated
        observation = self._observation()
        metrics = {
            "step": self._step_count,
            "elapsed_s": self._elapsed_s,
            "progress_m": self._unwrapped_progress,
            "route_progress_m": projection.distance_along,
            "lateral_offset_m": projection.lateral_offset,
            "distance_travelled_m": self._distance_travelled,
            "lap_complete": self._lap_complete,
            "failure_reason": self._failure_reason or ("step_limit" if truncated else ""),
            "route_seed": self._route_seed,
            "episode_seed": self._episode_seed,
        }
        return StepResult(observation, 0.0, terminated, truncated, metrics)

    def snapshot(self) -> dict[str, object]:
        """Private replay state, never supplied to policy or learning transitions."""
        if self.route is None or self.state is None:
            raise RuntimeError("reset must be called before snapshot")
        return {
            "step": self._step_count,
            "time_s": self._elapsed_s,
            "x_m": self.state.x_m,
            "y_m": self.state.y_m,
            "heading_rad": self.state.heading_rad,
            "speed_mps": self.state.speed_mps,
            "steering_rad": self.state.steering_rad,
            "progress_m": self._unwrapped_progress,
            "lap_complete": self._lap_complete,
            "failure_reason": self._failure_reason,
        }

    def replay_metadata(self) -> dict[str, object]:
        if self.route is None:
            raise RuntimeError("reset must be called before exporting replay metadata")
        return {
            "schema_version": 1,
            "route": {
                "frame": self.route.frame,
                "points": [[point.x, point.y] for point in self.route.points],
                "closed": True,
                "width": self.route.width,
                "width_source": self.route.width_source,
                "source": self.route.source,
            },
            "time_step_s": self._vehicle["time_step_s"],
            "vehicle": {key: self._vehicle[key] for key in sorted(_VEHICLE_FIELDS)},
            "observation": self._observation_settings,
            "effective_config": self.config.settings,
            "route_seed": self._route_seed,
            "episode_seed": self._episode_seed,
        }

    def outcome(self) -> dict[str, object]:
        return {
            "lap_complete": self._lap_complete,
            "terminated": self._terminated,
            "truncated": self._truncated,
            "failure_reason": self._failure_reason or ("step_limit" if self._step_count >= self._max_steps and not self._lap_complete else None),
            "steps": self._step_count,
            "elapsed_s": self._elapsed_s,
            "progress_m": self._unwrapped_progress,
            "distance_travelled_m": self._distance_travelled,
            "route_seed": self._route_seed,
            "episode_seed": self._episode_seed,
        }

    def _observation(self) -> Observation:
        assert self.route is not None and self.state is not None
        return build_observation(
            self.route, x_m=self.state.x_m, y_m=self.state.y_m,
            heading_rad=self.state.heading_rad, speed_mps=self.state.speed_mps,
            age_s=0.0, valid=True, settings=self._observation_settings,
        )


def _finite(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError):
        return False
