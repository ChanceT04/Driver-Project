"""T4A: connect a route, simulator and diagnostic driver for a visible episode."""
from __future__ import annotations
import json
import time
from pathlib import Path

from f1_agent.training.config import ProgramConfig
from f1_agent.environment.simulator import DrivingSimulator
from f1_agent.policy.baselines import RouteFollower, ZeroActionPolicy
from f1_agent.track.json_io import load_route
from f1_agent.training.interfaces import Action


def simulate(config: ProgramConfig, output_dir: Path, *, route_path: Path | None = None) -> None:
    """Create a new run, save replay and metrics. T4A requires --route; T4B adds generation."""
    if route_path is None:
        raise ValueError("T4A simulate requires --route; generated routes are added by T3")
    route = load_route(route_path)
    output_dir = Path(output_dir)
    # Validate all runtime settings and the fixed route before creating outputs.
    DrivingSimulator(config, lambda _seed: route)
    output_dir.mkdir(parents=True, exist_ok=False)
    vehicle = config.settings["vehicle"]
    observation = config.settings["observation"]
    follower = RouteFollower(
        wheelbase_m=vehicle["wheelbase_m"],
        max_steering_rad=vehicle["max_steering_rad"],
        speed_scale_mps=observation["speed_scale_mps"],
        target_speed_mps=min(5.0, vehicle["max_speed_mps"]),
        distance_scale_m=observation["distance_scale_m"],
    )
    results = {}
    for name, policy in (("follower", follower), ("zero_action", ZeroActionPolicy())):
        simulator = DrivingSimulator(config, lambda _seed, fixed=route: fixed)
        results[name] = _run_episode(simulator, policy, output_dir / ("episode.jsonl" if name == "follower" else "zero-action.jsonl"))
    departure_simulator = DrivingSimulator(config, lambda _seed: route)
    results["departure"] = _run_episode(
        departure_simulator, _DeparturePolicy(), output_dir / "departure.jsonl"
    )
    (output_dir / "summary.json").write_text(json.dumps({"schema_version": 1, "outcomes": results}, indent=2) + "\n", encoding="utf-8")


class _DeparturePolicy:
    """Deliberately unsafe fixed command used only for a recorded failure case."""

    def act(self, _observation: object, *, explore: bool = False) -> Action:
        return Action(steer=1.0, throttle=0.5, brake=0.0)


def _run_episode(simulator: DrivingSimulator, policy: object, path: Path) -> dict[str, object]:
    observation = simulator.reset(route_seed=0, episode_seed=0)
    started = time.perf_counter()
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        def write(record: dict[str, object]) -> None:
            stream.write(json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n")

        write({"type": "metadata", "schema_version": 1, **simulator.replay_metadata()})
        # Step zero is the recorded spawn frame; it has no action or outcome yet.
        write({"type": "step", **simulator.snapshot(), "action": None, "reward": 0.0, "terminated": False, "truncated": False})
        while True:
            action = policy.act(observation, explore=False)
            result = simulator.step(action)
            observation = result.observation
            write({
                "type": "step", **simulator.snapshot(),
                "action": {"steer": action.steer, "throttle": action.throttle, "brake": action.brake},
                "reward": result.reward, "terminated": result.terminated,
                "truncated": result.truncated,
            })
            if result.terminated or result.truncated:
                break
        outcome = simulator.outcome()
        elapsed = time.perf_counter() - started
        outcome["wall_time_s"] = elapsed
        outcome["steps_per_s"] = simulator._step_count / elapsed if elapsed > 0 else 0.0
        write({"type": "outcome", **outcome})
        stream.flush()
    return outcome
