# T4A — One visible driving loop

Status: Implemented — evidence pending (replay visual inspection). Dependencies: T1 reviewed / complete.

## Deliver

Complete the smallest useful offline driving program on T1's oval.

Owned files: `environment/dynamics.py`, `simulator.py`, `demo.py`,
`render.py`; introduce the initial shared observation in
`evaluation/observation.py` and diagnostic follower in `policy/baselines.py`.
Use the existing interfaces and CLI.

- Implement fixed-dt car pose/speed updates with steering, acceleration and braking.
  Validate the vehicle settings used here and state which later settings are deferred.
- Inject a fixed route provider into DrivingSimulator. Reset clears all episode state.
- Produce normalized local route preview, lateral/heading error and speed with validity
  fields using the architecture's v1 proposal. T5 will finalize/probe this contract.
- Implement a cautious route follower using only those observations. ZeroActionPolicy
  already exists. The follower is a diagnostic benchmark, not a learned agent.
- End on a real traversed lap, departure, stalled progress or time limit.
  Keep scoring/private state separate. Reward may be zero until T5.
- Complete `simulate --route ...`; save schema-v1 episode.jsonl and outcome.
- Complete `replay` with a simple top-down visual (portable HTML canvas is sufficient).
  Draw the route, synthetic road corridor, moving car and outcome.
  Rendering is optional and outside the physics step.

## Evidence

The CLI drives the oval with the follower and produces a replay showing a lap.
Show departure and stationary timeout cases as well. Check acceleration/braking,
steering sign, deterministic reset/replay, no instant lap completion at spawn,
and finish-line wrapping. Inspect the visual artifact, not just its existence.

Use new output directories under runs/. Do not require T3, T2, ML or game input.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Implement
`tests/test_simulator.py` and `tests/test_replay.py`; add initial observation
cases to `tests/test_observation.py`.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T4A-01 | Straight motion from (0,0), heading 0, speed 10 m/s, dt 0.1 s; disable drag, acceleration and steering | Next position (1,0), speed 10, heading 0 within 1e-8. With heading pi/2, next position is (0,1). |
| T4A-02 | From rest, acceleration 2 m/s^2, dt 0.1, ten full-throttle steps, no drag/caps reached; separately brake from 1 m/s with deceleration 5 m/s^2 for one second | Final acceleration-case speed is 2 m/s within 1e-8. Braking reaches zero without negative speed. Do not assume a position formula incompatible with the documented integration method. |
| T4A-03 | Mirrored left/right steering from heading zero at equal positive speed, before angle wrap | Negative Action.steer turns left (positive heading); positive steer turns right (negative heading). Mirrored states agree in forward displacement and oppose in lateral displacement within 1e-6. |
| T4A-04 | Reset twice with identical route/start seeds and replay 200 fixed actions | State, rewards and flags agree within 1e-8. A reset after a finished episode agrees with a fresh environment. Zero/negative dt and nonfinite physics settings fail explicitly. |
| T4A-05 | Spawn at finish line; remain stationary; leave the road; hit step limit; traverse the whole oval | Spawn/stationary behavior cannot complete a lap. Departure/stall terminate with correct reason; external limit truncates; only full forward traversal completes. No step continues an ended episode silently. |
| T4A-06 | Run follower from the standard oval start, and zero action from rest | Follower completes one valid lap within the declared episode budget. Zero action completes none. Save both outcomes; do not change the fixture after examining failure without recording it. |
| T4A-07 | Save and replay an episode; malformed version, empty/truncated replay, existing output file | Replay uses recorded states, even when physics stepping is mocked to fail. Reject unsupported/corrupt input clearly; preserve existing output bytes. |

Run focused checks for each of the three test files, followed by the existing
runner checks. Demonstrate these commands with fresh output names:

```powershell
python scripts/sim.py simulate --config configs/offline.example.json --route tests/fixtures/tracks/oval.json --output runs/t4a-drive
python scripts/sim.py replay runs/t4a-drive/episode.jsonl --output runs/t4a-drive/replay.html
```

Pass gate: numerical/episode checks pass and the oval lap is demonstrated.
Open the replay and inspect start, a bend, and finish: the car stays aligned
with recorded coordinates and outcome. Record screenshots or inspection notes.
If visual inspection is unavailable, report it pending; file existence is insufficient.

## Handoff

Report provisional physics settings, run/check commands, measured steps/second
and artifact paths. Identify assumptions for T4B and observation choices for T5.

## Implementation handoff — 2026-10-08

1. **Ticket / outcome:** T4A, implemented by `/root`. Numerical and episode
   checks pass. The HTML replay's required visual inspection remains pending, so
   this is not marked awaiting review yet.
2. **Behavior and changed files:** Added semi-implicit fixed-step bicycle
   dynamics, config checks, route-provider reset, wrapped signed progress,
   road-departure and stalled-progress termination, step-limit truncation,
   v1 local observations, an observation-only pure-pursuit follower and zero
   baseline. The CLI saves follower, zero-action and deliberate-departure
   episodes plus a summary. Replay validates schema-v1 JSONL and renders saved
   states in a portable canvas page without importing or rerunning physics.
   T4A changes: `src/f1_agent/environment/dynamics.py`,
   `src/f1_agent/environment/simulator.py`, `src/f1_agent/environment/demo.py`,
   `src/f1_agent/environment/render.py`,
   `src/f1_agent/evaluation/observation.py`,
   `src/f1_agent/policy/baselines.py`, `tests/test_simulator.py`,
   `tests/test_observation.py`, `tests/test_replay.py`, `README.md`, this ticket
   and `docs/tasks/README.md`.
3. **Acceptance cases:**

   | Case | Result | Evidence |
   | --- | --- | --- |
   | T4A-01 | Pass | `test_t4a_01_straight_motion_and_heading`; 1 m straight displacement at 10 m/s and both cardinal headings. |
   | T4A-02 | Pass | `test_t4a_02_acceleration_and_braking`; 2 m/s after ten steps and braking clamps at zero. |
   | T4A-03 | Pass | `test_t4a_03_steering_sign_and_mirror_symmetry`; left/right heading signs and mirrored displacement. |
   | T4A-04 | Pass | `test_t4a_04_reset_replay_and_invalid_physics`; identical 200-step traces, reset after finish equals fresh reset, invalid dt/settings reject. |
   | T4A-05 | Pass | `test_t4a_05_spawn_stall_departure_limit_and_end_guard`; spawn does not finish, stall/departure reasons, max-step truncation and ended-step guard. Final run also records departure, stall and completion outcomes. |
   | T4A-06 | Pass | `test_t4a_06_follower_completes_zero_action_does_not` and CLI run; follower completes with finish-line wrap, zero action stalls and does not finish. |
   | T4A-07 | Implemented — visual evidence pending | `test_t4a_07_saved_replay_is_physics_independent_and_rejects_bad_inputs` passes physics-mocked replay, unsupported version, empty/truncated input and sentinel overwrite checks. Replay CLI succeeds. Visual inspection could not be completed: the in-app browser blocked the local `file:` URL (only HTTP(S) is allowed); no alternate route was used. |

4. **Checks and measured results:** Python 3.12.14. The T4A focused commands
   exited 0: `test_simulator.py` (6 tests), `test_observation.py` (3 tests),
   and `test_replay.py` (1 test). Regressions exited 0: T1 `test_track_*.py`
   (8 tests), `test_training_framework.py` (6 tests), and
   `test_program_scaffold.py` (4 tests). `git diff --check` is recorded after
   final documentation edits below. CLI demonstration commands both exited 0:

   ```powershell
   & 'C:\Users\Chance Larson\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/sim.py simulate --config configs/offline.example.json --route tests/fixtures/tracks/oval.json --output runs/t4a-drive-reviewed
   & 'C:\Users\Chance Larson\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/sim.py replay runs/t4a-drive-reviewed/episode.jsonl --output runs/t4a-drive-reviewed/replay.html
   ```

   With route seed 0, episode seed 0 and the checked-in oval, the follower
   completed in **464 steps / 23.2 simulated seconds**, advancing 116.78 m;
   logged throughput was **3,393 steps/s including JSONL writing** on the final
   run. The zero-action baseline stalled at step 101 / 5.05 s. The deliberate
   departure ended at step 43 / 2.15 s. Summary and all three episodes are under
   `runs/t4a-drive-reviewed/` (ignored); replay is
   `runs/t4a-drive-reviewed/replay.html`. An initial failed bootstrap left the
   empty `runs/t4a-drive/` directory; it is retained and not used as evidence.
5. **Provisional settings and limitations:** Integration is semi-implicit
   Euler; acceleration is throttle-scaled, braking clamps speed at zero,
   quadratic drag uses the configured coefficient, steering angle follows the
   command immediately, and configured max speed is enforced. T4B owns steering
   response, command delay and lateral-acceleration/grip limits. T4A currently
   uses the example six lookaheads, divides distances by 100 m, speed by 40 m/s,
   uses zero reward and a fixed start; `episode_seed` is recorded but does not
   randomize that start. T5 must probe/finalize observation and reward behavior.
   The simulator is not calibrated to F1 physics; no learning or real-game
   validation was attempted. Next action: inspect replay start, a bend and finish
   in a permitted local viewer, then update the evidence status for review.
