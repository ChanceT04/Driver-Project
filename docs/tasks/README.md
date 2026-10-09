# Developer task index

This is the authoritative task order and status page. Existing ticket numbers
are retained so earlier handoffs remain recognizable. T4 is now T4A/T4B; T10
is the complete offline-program integration milestone.

Agents picking up work should read [the agent start guide](../../START_HERE.md)
for how to select an authorized ticket, track its status and return completed work.

## Current state

T1 route geometry, JSON import/export and its synthetic oval are implemented
and reviewed. The telemetry tools and generic training runner also contain real implementation.
Package setup, CLI routing and shared config checks work. Driving/perception
modules contain explicit proposed interfaces awaiting implementation.
No car has been simulated or policy trained in this scaffold.

Scaffold verification on 2026-10-08: 22 unit tests ran; 21 passed, including all
four program-scaffold and six runner checks. The existing UDP datagram-capture
test failed with zero received packets versus two expected; see the telemetry
notes before claiming the entire suite passes. All 40 package modules imported,
both declared console entry points resolved, and 25 local Markdown links resolved.
Five unfinished commands returned an explicit error without creating fake output.
Package installation, car physics, rendering and learning have not been verified.

## Offline program sequence

**T1 -> T4A -> T3 -> T4B -> T5 -> T6 -> T10**

T3 may be implemented after T1 independently of T4A. The recommended order
above gets a visible car moving before expanding the track distribution.
T2 can run after T1 but does not block simulator training.

Every ticket has numbered required acceptance cases, named test files,
expected results and a demonstration/pass gate. Read [testing and acceptance](../testing.md)
alongside the assigned ticket. T1's feature tests have passed review; other
feature tickets remain pending. Existing scaffold verification above is separate.

| Ticket | Deliverable / done when | Prerequisites | State |
| --- | --- | --- | --- |
| [T1](T1-track-contract-importer.md) | Valid route geometry + JSON + tiny oval fixture | None | Reviewed / complete |
| [T4A](T4A-minimal-driving-loop.md) | Car follows a fixture loop; saved episode visibly replays | T1 | Implemented — evidence pending (replay visual inspection) |
| [T3](T3-procedural-tracks.md) | Reproducible varied loops + preview + separate layout splits | T1 | Pending |
| [T4B](T4B-generated-track-simulator.md) | Generated-track episodes, response/grip limits, measured speed | T4A, T3 | Pending |
| [T5](T5-observation-evaluation.md) | Final observation, reward, metrics and baseline comparisons | T4B | Pending |
| [T6](T6-first-learning-experiment.md) | Actual learning, reloadable policy, validation results | T5 | Pending |
| [T10](T10-offline-program-integration.md) | Complete program workflow and unseen-track/stress evidence | T6 | Pending |

## Game integration branch

| Ticket | Deliverable | Prerequisites | State |
| --- | --- | --- | --- |
| [T2](T2-full-map-perception.md) | Real-image route/triangle extraction with overlays | T1 | Pending |
| [T7](T7-synchronized-capture.md) | Same-session screen/UDP evidence | T2 | Pending |
| [T8](T8-live-observation-adapter.md) | Calibrated, timestamped common observations | T5, T7 | Pending |
| [T9](T9-supervised-control-trial.md) | Supervised game-control experiment | T10, T8, explicit input authorization | Future |

T2 is an early feasibility check for eventual game transfer. Failure there does
not invalidate the ability to train in simulation, but it must be resolved before
promising that the learned driver can receive usable information from F1.

## Code ownership

All primary paths below exist. They contain interface scaffolding unless marked implemented.

| Owner | Primary files under src/f1_agent/ |
| --- | --- |
| T1 | track/geometry.py, track/json_io.py |
| T4A | environment/dynamics.py, simulator.py, demo.py, render.py; initial evaluation/observation.py and policy/baselines.py |
| T3 | track/procedural.py |
| T4B | environment/dynamics.py, simulator.py, demo.py; randomization settings |
| T5 | evaluation/observation.py, metrics.py; environment/reward.py; policy/baselines.py |
| T6 | policy/model.py, training/sim_train.py; targeted integration updates to training/experiment.py |
| T10 | evaluation/robustness.py; end-to-end checks, proven config and user instructions |
| T2 | perception/hud_route.py, player_marker.py |
| T7 | telemetry/session.py, synchronized_capture.py |
| T8 | runtime/observation_adapter.py |
| T9 | control/adapter.py |

Shared implemented files: `cli.py`, `training/config.py`,
`training/interfaces.py`, `training/experiment.py`.
The base project has `pyproject.toml`, `scripts/sim.py` and an example JSON config.
Feature owners complete relevant config validation and CLI integration; no new
parallel command framework is needed.

Keep existing implemented telemetry capture/decoder/report and human-lap dataset
exporter. The latter remains useful for later imitation or dynamics analysis.

## Handoff rules

Read the assigned ticket, [architecture](../architecture.md), relevant modules,
and root agent instructions. An assignment authorizes its implementation and
listed checks; no additional confirmation is needed for routine work in that scope.
A task list alone does not assign every ticket.

Implement one assigned unit, including its command path and meaningful evidence.
Replace unfinished bodies; do not count importing modules or help output as feature
completion. Add focused tests when implementing behavior, not empty test files now.
Keep shared interface changes coherent across callers.

Update this index's state and append a brief handoff to the ticket: changed files,
exact checks/exit codes, outputs and measured results, limitations, and next unblock.
Mark work implemented/awaiting review until reviewed. Keep changes uncommitted unless
the user asks otherwise. Never label stub results or synthetic checks as real-game proof.
