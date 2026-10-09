"""T4A/T4B: pure 2D vehicle stepping, independent of reward and rendering."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from f1_agent.training.interfaces import Action


@dataclass(frozen=True)
class VehicleState:
    """Map metres, radians (counterclockwise), metres/second; x right, y up."""
    x_m: float
    y_m: float
    heading_rad: float
    speed_mps: float
    steering_rad: float = 0.0


def advance(state: VehicleState, action: Action, parameters: Mapping[str, object]) -> VehicleState:
    """One fixed step. T4A starts simple; T4B adds response and grip limits.

    Action.steer is positive RIGHT; heading is positive counterclockwise.
    Apply the sign conversion once here. Command-delay state belongs to the
    environment, so this function remains deterministic and stateless.
    """
    required = {
        "time_step_s", "wheelbase_m", "max_steering_rad",
        "max_acceleration_mps2", "max_braking_mps2", "max_speed_mps",
        "drag_coefficient_per_m",
    }
    if not isinstance(parameters, Mapping) or not required <= parameters.keys():
        raise ValueError("vehicle parameters are missing required T4A settings")
    values = {name: parameters[name] for name in required}
    if any(not _finite(value) for value in values.values()):
        raise ValueError("vehicle physics settings must be finite numbers")
    dt = float(parameters["time_step_s"])
    wheelbase = float(parameters["wheelbase_m"])
    max_steering = float(parameters["max_steering_rad"])
    max_acceleration = float(parameters["max_acceleration_mps2"])
    max_braking = float(parameters["max_braking_mps2"])
    max_speed = float(parameters["max_speed_mps"])
    drag = float(parameters["drag_coefficient_per_m"])
    if dt <= 0 or wheelbase <= 0 or max_speed <= 0:
        raise ValueError("time_step_s, wheelbase_m and max_speed_mps must be positive")
    if min(max_steering, max_acceleration, max_braking, drag) < 0:
        raise ValueError("steering, acceleration, braking and drag settings must be nonnegative")
    if max_steering >= math.pi / 2:
        raise ValueError("max_steering_rad must be less than pi/2")
    if not isinstance(state, VehicleState) or any(not _finite(value) for value in (
        state.x_m, state.y_m, state.heading_rad, state.speed_mps, state.steering_rad
    )) or state.speed_mps < 0:
        raise ValueError("vehicle state must contain finite values and nonnegative speed")
    if not isinstance(action, Action):
        raise TypeError("action must be an Action")

    # Semi-implicit Euler: update speed, then heading, then position. Drag is a
    # quadratic speed loss; braking cannot push the car below zero.
    acceleration = action.throttle * max_acceleration - action.brake * max_braking
    acceleration -= drag * state.speed_mps * state.speed_mps
    speed = min(max_speed, max(0.0, state.speed_mps + acceleration * dt))
    steering_angle = action.steer * max_steering
    heading = state.heading_rad - (speed / wheelbase) * math.tan(steering_angle) * dt
    x = state.x_m + speed * math.cos(heading) * dt
    y = state.y_m + speed * math.sin(heading) * dt
    return VehicleState(x, y, heading, speed, steering_angle)


def _finite(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError):
        return False
