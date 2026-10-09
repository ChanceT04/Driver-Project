# T5 — Observations, rewards and baseline evaluation

Status: pending T4B. HUD extraction is not a prerequisite.

## Deliver

Finalize `evaluation/observation.py`, `metrics.py`,
`environment/reward.py`, and diagnostic `policy/baselines.py`.

- Freeze the architecture's v1 observation schema, fixed shapes, normalization,
  sign conventions, age and missing-value behavior. Validate observation config.
- Check that the policy cannot access absolute position, track ID, true road width,
  exact progress or other private state. The live adapter will later use this schema.
- Implement reward from newly earned forward progress, time cost, departure and
  completion. Validate weights and probe stopping, reversing, shortcuts and repeated
  crossing/oscillation. Keep evaluation success separate from reward.
- Implement evaluate without a checkpoint: compare zero action and route follower on
  fixed validation episodes. Baselines need act only; adapt the evaluator cleanly
  rather than giving them fake learning/checkpoint methods.
- Return progress_m and lap_complete plus outcome reason, elapsed time and smoothness
  metrics from simulator steps. Aggregate completion counts/rates, failure distance,
  valid-lap time and spread. No completed laps means null lap time, never zero.

## Evidence

Focused schema/sign/wrap/invalid-data checks and reward-exploit cases.
Produce a baseline report and example replays on varied generated routes using
identical reset conditions. Include failures and denominators.

T2's raw HUD output can be inspected separately in pixels. Do not fabricate metre
scale or speed to claim that it already matches full simulator observations; T8
owns the calibrated real-data check.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Complete
`tests/test_observation.py`, `tests/test_reward.py` and
`tests/test_evaluation.py`.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T5-01 | Metre route with a long +x straight, car (0,0) heading 0; lookaheads 5/10 m, distance scale 100, speed 20 and speed scale 40 | Preview ((0.05,0),(0.10,0)), speed 0.5, lateral/heading error 0 within 1e-8. Use an independently constructed route with sufficient straight length. |
| T5-02 | On that straight, car shifted to y=2, first lookahead measured from its route projection | Lateral error +0.02 and first preview (0.05,-0.02). Rotate route and car together by pi/2 and translate both: observations are unchanged within 1e-8. |
| T5-03 | Same route centreline/pose with different synthetic width, route identifier/provenance or private metrics; also raw-pixel route and missing speed | Width/identity/metrics never enter or alter policy observations. Reject uncalibrated pixel route. Missing speed sets speed_valid false with the documented finite placeholder; pose validity remains independent. |
| T5-04 | Reward weights progress=1, time=0.05/s, departure=10, lap bonus=50; 2 m new progress over 1 s | Ordinary reward 1.95; departure case -8.05; legitimate completion case 51.95, within 1e-8. Stationary step yields -0.05. Reject nonfinite inputs/weights. |
| T5-05 | Forward/backward oscillation over already visited progress, reverse lap, finish-line crossing without traversal, interior shortcut | Previously earned progress is not rewarded again and no completion bonus occurs. Repeated cycling cannot keep increasing return from re-earned progress. Test simulator progress plus reward together, not just a mocked progress argument. |
| T5-06 | Four outcomes: valid laps at 10/14 s, failures after 20/40 m | Completion 2/4=0.5, median valid-lap time 12 s, mean failure distance 30 m. All-failure batch has null valid-lap time; empty batch is explicitly rejected or represented with count 0 and undefined rates, never 100%. |
| T5-07 | Evaluate a fake policy whose learning hooks raise; record every route/start request | No learning hook is called; comparisons receive identical routes/starts. Re-evaluation is deterministic. Constant actions have zero smoothness cost under the documented metric. |

Run the three named test files and existing runner tests. Run CLI baseline
evaluation on the same 20 validation attempts established in T4B. Zero action
from rest must complete zero laps; the follower must retain its easy-oval success.
Report all generated-route results without requiring a particular completion
rate yet.

Pass gate: exact observation/reward/metric cases and exploit checks pass; provide
one completion replay and one failed/zero-action replay to inspect alongside the report.

## Handoff

Report the final observation contract, reward settings, baseline results and
remaining environment defects. T6 selects the learning method using this evidence.
