# T8 — Real-time observation adapter

Status: **planned; assign after T5 and T7 review**.

Implement `runtime/observation_adapter.py`. T5 no longer depends on HUD parsing:
this ticket owns the first complete real/simulator observation equivalence check,
including metric calibration. Raw pixel previews from T2 are not metre observations.

## Objective

Convert the live HUD map/triangle and UDP vehicle data into T5 observations, with explicit uncertainty and measured age. This remains read-only.

## Work

- Reuse T2 route and marker extraction on T7's synchronized capture, then on live frames if stable. Decode the relevant player telemetry without coupling image processing to the UDP receive loop.
- Estimate map scale and orientation using same-session track length and motion/marker correspondences. Check whether heading sign and progress direction agree. Report fit error and reject inconsistent calibrations. Treat route length as provisional until this check succeeds.
- Publish timestamped T5 observations. Flag stale frames, marker misses, missing packets, uncertain scale, and impossible position jumps; do not silently substitute simulator state or an old pose.
- Make HUD crop/resolution configuration explicit. A changed HUD layout must fail visibly or require recalibration, not produce plausible-looking wrong steering inputs.

## Acceptance evidence

- Replay the synchronized capture and show observation age distribution, map-to-world residuals, route progress continuity, and missing-data rates. Inspect examples from straights and corners.
- Compare a short live read-only run with replay. No policy may send actions in this ticket.

## Out of scope

Training and game input. If the full map fails on another circuit, document the failure and return to the perception decision before connecting control.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Implement
`tests/test_live_observation.py` with fake clocks and small calibration fixtures.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T8-01 | At least three noncollinear HUD/world correspondences from a known transform containing pixel y-flip, rotation, translation and scale | Recover held-out positions within 1e-6 m on exact synthetic data. Cardinal headings map to correct orientation/sign; scale remains positive. Collinear/insufficient or inconsistent correspondences reject calibration. |
| T8-02 | One metre route/pose supplied directly to the common builder, then the equivalent synthetic HUD+UDP inputs through the adapter | All normalized observation fields and validity flags agree within 1e-6. No width, identity or absolute coordinates appear in the policy observation. |
| T8-03 | Stale threshold 0.5 s; frame age 0.499 then 0.501 s, missing marker, missing speed, and clock reversal | First pose fresh, second stale/invalid; pose/speed flags reflect separate availability. No stale pose is relabelled fresh. Negative age/clock reversal is rejected or explicitly invalid. |
| T8-04 | Frame time 1.0 s; UDP samples at 0.9 and 1.1 s | Live causal observation uses no sample from the future. Document alignment/age policy and verify source timestamps in diagnostics. Offline interpolation, if implemented, is explicitly a separate mode. |
| T8-05 | Resolution/crop change, session switch and physically impossible marker jump | Calibration is invalidated or the observation rejected. The previous calibration/pose cannot silently produce valid control input for a changed session/layout. |
| T8-06 | Same-session capture replayed twice with a controlled clock | Identical observations/validity decisions, except explicitly excluded host timing fields; no controller is connected. |

Run:
`python -m unittest discover -s tests -p "test_live_observation.py" -v`
plus common-observation and perception tests.

Real-input gate: use T7's synchronized recording. Fit calibration on an initial
segment containing distinct directions; assess on a separate later segment, never
the same samples used to fit. Report median/95th-percentile position/heading
residuals, observation age, valid fraction and discontinuities. Inspect at least
three straights and three corners where the recording supports them.

Before scoring, record a metre/heading/age error budget justified by T4B/T10
sensitivity experiments; a fixed claim of adequate accuracy from fit error alone
is insufficient. If that evidence or suitable recording is missing, mark calibration
acceptance pending. Then compare at least 30 seconds of read-only live observations
against replay behavior. No game inputs are part of these checks.
