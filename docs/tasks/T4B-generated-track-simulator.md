# T4B — Simulator across generated tracks

Status: pending T4A and T3.

## Deliver

Extend the existing T4A implementation in `environment/dynamics.py`,
`simulator.py` and `demo.py`. Do not build a second simulator.

- Use generate_route as the injected route provider; enable simulate without --route.
- Complete vehicle config validation and tunable steering response, drag, grip/turn
  limits and optional control delay. Provisional defaults are not F1 calibration.
- Support seeded starts along the route, lateral/heading perturbations and configured
  grip/delay variation. Keep route layout seed independent of episode seed.
- Define whole-lap progress from arbitrary starts with continuous traversal checks.
  Prevent route-projection jumps and finish-line oscillation from creating progress.
- Keep privileged width/bounds/progress in metrics and replay, out of observations.
- Reset all history and pending inputs. Support thousands of headless episodes.

## Evidence

Run the diagnostic follower across generated validation layouts, reporting every
attempt and failure. Check deterministic replay, delayed-input reset, turning limits,
random-start lap counting, departure and timeouts. Measure steps/second and episode
throughput on this machine with rendering disabled. Profile only observed bottlenecks.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Extend
`tests/test_simulator.py` and add `tests/test_simulator_variation.py`.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T4B-01 | Same route seed, different episode seeds; then exactly repeated pairs | Episode variation changes only enabled start/dynamics settings, not route geometry. Repeated seed pairs reproduce the trajectory within 1e-8. All-disabled variation gives the base configuration. |
| T4B-02 | dt=0.05 s and command delay=0.10 s; apply one steering/throttle pulse after neutral input | No pulse is applied earlier than the declared two-step delay. Assert exact application index under the documented time convention. Reset with a pending pulse, then feed neutral: no old command survives. |
| T4B-03 | Steering step, drag-only coasting and excessive requested turn rate at positive speed | Steering approaches its target within the stated response model; drag cannot accelerate the car. Applied speed*abs(yaw_rate) respects the configured lateral-acceleration bound plus numerical tolerance. |
| T4B-04 | Start at 0%, 25% and 90% of the loop; replay known continuous progress samples | Each requires one full forward traversal from its own start. Moving across the map's global finish line early does not finish the lap. |
| T4B-05 | Repeated movement either side of finish line, reverse travel, nearby-branch projection jump, shortcut across the interior | No false lap and no unearned forward progress. Exercise progress accounting directly with independently constructed trajectories; do not require an ML policy to find the exploit. |
| T4B-06 | Invalid/randomization ranges, negative delay, unsupported config key | Clear error before output creation. Every enabled parameter affects its documented behavior; no silently ignored settings. |

Run both simulator test files and the T4A replay/observation checks.

Integration gate: run the follower on 10 fixed validation routes with two
predeclared valid starts each (20 attempts). All attempts end within the budget,
with finite states and an explicit outcome. Report completion as a measurement;
no required 20/20 success or hidden removal of difficult tracks. T4A's easy oval
must still complete.

Benchmark three batches of at least 10,000 headless steps, excluding startup and
rendering; report median/range and machine details. Aim for at least 10x simulated
real time. This is an initial performance target, not an observed capability:
below-target results require an identified bottleneck and senior review before
launching long training, without weakening correctness checks.

## Handoff

Provide supported configuration, actual throughput and failure cases. T5 uses these
results to decide whether the environment is ready for meaningful learning.
