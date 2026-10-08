# Architecture proposal

## Goal

Build an autonomous driver for private, offline F1 25 sessions. First prove that telemetry is timely and usable, then build a repeatable benchmark, map one circuit, and evaluate increasingly capable drivers. The success metric is valid lap performance and consistency; the human lap is a starting demonstration and benchmark, not a target ceiling.

## Runtime data flow

F1 25 UDP output -> telemetry receiver/decoder -> timestamped recorder -> track/map alignment and evaluation -> (later) driver policy -> (later) isolated controller adapter -> F1 25.

A separate training path consumes recorded data or a fast simulator, trains a policy, and stores versioned checkpoints under `runs/`. The game-facing runtime must not block on training or logging.

## Module responsibilities

- `telemetry/`: UDP socket, packet validation/decoding, event timing, recorder, and packet-health measurements. Initial phase is read-only.
- `track/`: selected track identity, coordinate conventions, map loading, interpolation, and position-to-track alignment. Track data carries source and attribution metadata.
- `evaluation/`: lap validity, completion rate, lap and sector times, packet quality, and comparisons against the fixed baseline.
- `control/`: later controller interface and input adapter. No game inputs in the feasibility phase.
- `environment/`: later training-environment interface and simplified vehicle/track simulation if measurements justify it.
- `policy/`: later observation/action definitions and saved-driver inference.
- `training/`: later learning algorithm, replay/data pipeline, checkpoints, and training metrics.

## Data contracts

- Units are explicit (metres, metres/second, radians, seconds, normalized controls).
- Keep game session time/frame identifier separate from local monotonic receive time.
- Store raw packets or lossless captures separately from decoded tables so parser changes can be checked later.
- Observations and actions have versioned schemas before any trained policy is connected to the game.
- Every experiment records track, car, setup, assists, weather, session mode, software revision, and checkpoint identity.

## Reproducibility and boundaries

`configs/` holds reviewed experiment settings. `data/maps/` holds map assets plus provenance. `data/telemetry/` and `runs/` are local working data and ignored by Git. Source, documentation, configuration examples, and small synthetic fixtures may be committed.

The first dependency is a minimal Python telemetry receiver. Controller input, simulator implementation, and RL algorithm selection are later decisions, made from feasibility measurements rather than assumed now.

## Open decisions

1. Select the first circuit and confirm available map coverage and quality.
2. Confirm game telemetry format/rate and measure actual arrival jitter and packet loss.
3. Measure controller response and repeatable offline restart behavior before building an automated driver.
4. Compare CPU and supported AMD GPU training for the eventual low-dimensional policy on this PC.
5. Choose direct in-game learning, simulator pretraining, or a hybrid after measuring model fidelity and attempt reset cost.
