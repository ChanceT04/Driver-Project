# T9 — Supervised offline control trial

Status: **future; requires explicit user assignment and authorization to send game inputs**.

Dependencies: T10's reviewed offline policy/results and T8's calibrated live
observations. Implement the existing `control/adapter.py` boundary. Importing
the package or running the offline simulator must never connect to a controller.

## Objective

Measure whether we can send repeatable steering, throttle, and brake commands in a private offline session, then attempt a deliberately cautious closed-loop run using the T6 policy and T8 observations.

## Work

- Build a narrow controller adapter with normalized actions, output clamping, rate limits, command timestamps, a visible hard stop, and a timeout that returns controls to neutral when observations are stale or missing. Keep it isolated from training and logging.
- First measure applied-control response and command-to-telemetry delay using small supervised inputs in a safe offline context. Establish restart/recovery behavior before attempting a lap.
- Evaluate the frozen T6 policy on a track withheld from training at a conservative speed cap. Record valid-lap status, distance reached, failures, interventions, latency, and checkpoint/config identity. Keep human supervision and an immediate stop path throughout.
- Use failures to decide whether to revise perception, simulator dynamics, training distribution, or controller timing. Do not tune on the final held-out test track and then continue calling it unseen.

## Acceptance evidence

- Exact input path and measured delay, a demonstrated hard stop/failsafe, and a report of every trial rather than only the best attempt.
- A completed valid lap is a milestone, not a prerequisite for reporting useful results. If control is unreliable, stop the closed-loop attempt and report the cause.

## Boundaries

No multiplayer, leaderboard submissions, unattended runs, game-file edits, or game-setting changes are authorized by this plan. Do not begin this ticket from the planning document alone.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Implement
`tests/test_control_adapter.py` with a fake backend and fake clock first.
Real-input tests still require the ticket's explicit user authorization.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T9-01 | Import package and construct controller, without connect | No backend connection or emitted input. Applying before connect fails clearly. Offline simulator commands never call connect/apply. |
| T9-02 | Normalized extrema and neutral actions through backend conversion | Steering left/centre/right and throttle/brake endpoints map to documented backend ranges. Invalid raw values are rejected before constructing Action; no nonfinite or out-of-range backend command escapes. |
| T9-03 | Rate limit 2 steering units/s, dt=0.1 s, request +1 from previous 0 | Output steering changes by at most 0.2 per step, with the correct sign. No timestamp means no invented dt that bypasses limiting. |
| T9-04 | Set stale timeout=0.2 s; last observation at t=0; advance fake clock past 0.2 s without further apply calls | Independent watchdog emits neutral controls and inhibits further stale actions. The stop mechanism cannot depend on the stalled inference loop calling apply again. |
| T9-05 | Hard stop during nonneutral output, backend write exception, shutdown, repeated stop/close | Neutralization/release is attempted, resources close, failures remain visible and no later queued driving command is emitted. Repeated cleanup is safe. A failed backend must never be reported as successfully neutralized. |
| T9-06 | Missing/invalid observation, incompatible checkpoint or calibration invalidation | Driving does not begin/continue; explicit fault and neutral/stop behavior under the documented adapter contract. |

Run:
`python -m unittest discover -s tests -p "test_control_adapter.py" -v`.
All fake-backend checks must pass before a real-input trial.

Authorized real-input gate: demonstrate neutral startup, left/right sign,
throttle/brake response, hard stop and stopped-inference timeout in a supervised
offline session. Measure command-to-telemetry delay for at least five bounded input
changes, reporting distribution and failures. Establish reset/recovery procedure
before attempting a lap.

Record every closed-loop attempt, checkpoint/config identity, interventions and
game lap-validity status. A valid autonomous lap requires completion with no
human driving intervention during that attempt; assisted attempts remain useful
but are labelled assisted. Input-adapter completion and successful driving are
separate outcomes. No synthetic backend test proves actual game input behavior.
