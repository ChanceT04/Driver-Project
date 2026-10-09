# Program architecture and shared contracts

## Target

The complete offline program generates varied tracks, simulates steering,
throttle and braking, trains a learned driver, saves reloadable policies, and
reports lap completion on whole unseen tracks. A replay lets us inspect failures.
Training runs without rendering or the F1 game.

The separate game branch extracts the full HUD route and player triangle,
combines them with UDP motion data, and supplies the same policy observation.
A simulator result alone does not establish successful transfer.

## Assembly

```text
CLI + config
  -> route provider (fixed JSON first, procedural generator next)
  -> DrivingSimulator.reset / step
       -> dynamics + route projection + episode termination
       -> common observation -> policy.act -> Action -> next step
       -> private progress/failure state -> reward and metrics
  -> training runner -> transitions -> learned agent updates
  -> checkpoints + episode results + selected replays
  -> frozen evaluation on validation / final test routes

Later:
HUD route + triangle + synchronized UDP
  -> calibrated live observation -> same frozen policy -> authorized game adapter
```

The shared interfaces already exist in `training/interfaces.py`. Feature
modules now contain proposed public entry points with explicit
`NotImplementedError` bodies. Implement those in the assigned tickets;
coordinate necessary API changes with their callers instead of building a
parallel framework.

## Ownership and dependency rules

- Track geometry has no dependency on simulator, image processing or ML.
- Dynamics advances a vehicle state and has no renderer, reward or game connection.
- Simulator receives a route provider callable. T4A can use a fixed fixture
  before T3 implements generation.
- Observation construction takes route/pose/speed values, so both simulator
  and live adapter can call it. It does not import simulator state types.
- Policy sees only observations and training transitions. Simulator snapshots
  and metrics remain private to evaluation/replay.
- The diagnostic follower uses the policy observation; it does not read future
  simulator state. It is a benchmark and a possible future demonstration source.
- CLI routes to feature modules. Feature validation happens before creating
  outputs. Outputs must not overwrite previous runs.
- Rendering is optional and outside the physics/training hot path. Replay uses
  recorded states instead of rerunning possibly changed physics.
- Begin with a feed-forward policy. Recurrent policies would require explicit
  episode reset/state handling and are not implied by the current interface.

## Coordinates and actions

| Quantity | Contract |
| --- | --- |
| HUD route | Pixels, x right and y down; no implicit metre conversion |
| Simulator/map route | Metres, x right and y up |
| Route direction | Ordered points define travel direction |
| Route storage | Explicit closed loop; accept and normalize a repeated endpoint; T1 fixes JSON details |
| Lateral error | Positive left of route travel, negative right |
| Map heading | Radians, positive counterclockwise from +x |
| HUD heading | atan2(dy, dx) in pixels; live adapter converts axes and orientation |
| Local preview | Forward and left distances relative to the car |
| Steering action | -1 left, +1 right; dynamics converts to the map heading convention |
| Throttle/brake | Each 0..1 |
| Time and speed | Seconds and metres/second internally |

`Action` rejects invalid/nonfinite commands. Policy output conversion must
bound values before constructing it; do not write a simulator test expecting
an invalid `Action` to survive construction.

The HUD line is a route guide. Its thickness does not measure road width.
Generated road width is synthetic and is used privately for departure scoring.
A pixel route must remain in pixels until same-session calibration is available.

## Observation v1 proposal

T4A implements the minimum needed to drive; T5 freezes and verifies this schema.
T8 supplies it from real data. Configure the lookahead distances once and store
them with the checkpoint.

| Field | Representation |
| --- | --- |
| schema_version | 1 |
| route_preview | Fixed-length sequence of (forward, left), divided by distance_scale_m |
| lateral_error | Signed metres divided by distance_scale_m |
| heading_error | Wrapped route-minus-car heading divided by pi |
| speed | Metres/second divided by speed_scale_mps |
| pose_valid / speed_valid | Explicit validity flags |
| observation_age_s | Age on the local monotonic clock, seconds |

Model packing has a fixed documented order and is owned by T6. Missing numeric
fields use a documented finite placeholder only with their validity flag false.
Age must be finite and nonnegative. Bad observations must never silently appear
fresh and valid. No track ID, absolute coordinates, total route progress, exact
road bounds or future physics belong in policy input.

Raw HUD previews from T2 remain diagnostic pixels; they cannot be passed into
this metre-based observation by assigning a fake scale.

## Episodes, rewards and measurement

Reset separates route seed from episode/start-state seed. T4A begins with a
known start and a fixed loop. T4B adds generated routes and varied starts. A lap
requires continuous forward traversal of the whole loop, including checkpoint
or equivalent continuity checks; crossing a start line alone is insufficient.

Completion, departure and prolonged lack of progress terminate an episode.
An external time/step limit truncates it. Learning must bootstrap truncations
appropriately for the chosen method. All delay queues and progress counters
reset between episodes.

T4A may return zero reward while establishing physics. T5 owns the first reward:
new forward progress, a small elapsed-time cost, departure penalty and completion
bonus. Verify reversing, shortcuts, re-crossings and stationary oscillation.
Reward totals do not replace measured valid-lap completion.

Required metrics: completion count/rate with denominator, distance before failure,
failure reason, elapsed time, median time for completed laps (null if none),
and action smoothness. Keep full attempt counts, including failed attempts.

## Configuration and artifacts

`configs/offline.example.json` defines the shared envelope. Its values are
unmeasured prototype settings. `training/config.py` currently checks the schema,
section objects and experiment bookkeeping, including disjoint seed sets.
Each ticket must reject unsupported keys and invalid values in its own section
before using them.

| Section | Owner |
| --- | --- |
| experiment | Existing runner; T6 integration and T10 final acceptance |
| track | T3 |
| vehicle | T4A minimal settings; T4B all dynamics settings |
| observation | T4A minimum; T5 complete contract |
| reward | T5 |
| agent | T6; null method deliberately means unselected |
| randomization | T4B support; T10 measured stress ranges |

One new directory per experiment under `runs/<name>/`:
- `resolved-config.json`: every actual setting, seeds, schema versions and dependency versions.
- `config.json`: existing runner's experiment settings.
- `episodes.jsonl`: existing runner's episode summaries.
- `checkpoints/` and `policy`: algorithm-owned checkpoint format documented by T6.
- `summary.json` and learning-curve artifact: aggregates with counts and split identity.
- `replays/`: a small selected set of driving episodes, with failures included.

T4A diagnostic runs write `episode.jsonl` directly under their output directory.
Replay schema v1 begins with metadata including route geometry/units, fixed dt
and full effective config; step records include time, vehicle state, action,
reward, and termination/failure status. A final record records the outcome.
T4A implements and documents exact fields. T6 can reuse this format for selected
episodes without logging every training step.

## Training and proof of completion

Use whole generated layouts for splits, never adjacent frames from the same lap.
Disjoint seeds are necessary but T3 must also reject duplicate/equivalent layouts.
Inspect layout diversity so a few similar loops do not masquerade as generalization.

Choose a small learning method after baseline and throughput measurements.
Imitation from the diagnostic follower, reinforcement learning, or an imitation
warm start followed by reinforcement learning remain options. Record the chosen
method and its evidence in the T6 handoff.

The current generic runner always tests the final in-memory policy once per
invocation. T6 must add a validation-only development path, declare checkpoint
selection (final fixed-budget or validation-selected), reload that candidate, and
keep final test evaluation separate. Do not repeatedly tune against test results.

T10 completes integration: fresh setup, generated-track preview, baseline episode,
real training, checkpoint reload, frozen evaluation, replay, and robustness results.
Report actual throughput and learning outcomes. A functioning trainer with failed
learning is an honest engineering result, but the driver milestone also requires
measurable held-out improvement.
