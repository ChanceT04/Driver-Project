# T10 — Complete offline program and robustness evidence

Status: pending T6. This finishes the simulator/trainer milestone before game control.

## Deliver

Own `evaluation/robustness.py`, a documented runnable config under configs/,
focused end-to-end checks and final README workflow. Integrate robustness into the
evaluation CLI (add --suite robustness or an equally small explicit option).

- Verify fresh-environment install and existing source-checkout commands.
- Run track preview, a baseline driving episode, real training, checkpoint reload,
  frozen evaluation and saved-episode replay without manual source edits.
- Supply one quick smoke configuration and one measured training configuration.
  Document actual hardware, elapsed time and throughput; avoid invented runtimes.
- Stress the frozen candidate on validation scenarios varying corner patterns,
  width, initial pose, grip, command delay and observation noise/missingness.
  Keep each scenario reproducible and report full failure counts.
- Make the declared checkpoint selection using validation only. Freeze settings
  before a final test on whole withheld layouts. Report initial/final policy and
  diagnostic baselines under the same test conditions.
- Check all configuration sections are actually validated and used, outputs cannot
  overwrite previous runs, useful error messages survive a fresh process, and no
  simulator path imports a real game-control backend.
- Replace scaffold-only instructions with measured commands as features become real.

## Acceptance

Engineering completion requires one documented workflow that trains, saves,
reloads, evaluates and visibly replays a driver on generated tracks.
Learning success additionally requires evidence of improved unseen-track completion
over the initial policy/zero-action baseline, with counts and seed spread.
A follower can remain stronger than the first learned policy; disclose that result.

Set the concrete acceptance suite and desired completion threshold before the final
test, using validation feasibility. Do not silently lower it after viewing test results.
If improvement is absent, report the functioning software separately from the
unmet driving milestone and open a bounded corrective experiment.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Implement
`tests/test_offline_workflow.py` and `tests/test_robustness.py`.
Keep the small software smoke workflow separate from longer learning experiments.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T10-01 | Fresh environment, declared dependencies only; install package; invoke source and installed entry points | Both routes execute the documented preview -> simulate -> train -> reload/evaluate -> replay workflow, with no source edits and no game running. Record exact interpreter/dependency versions. |
| T10-02 | Short smoke training, then evaluate its saved policy in a fresh process | At least one real update; finite results; consistent checkpoint/schema/config identity in reports. Reload checks from T6 pass. Smoke duration is measured; no learning-quality claim is inferred from a tiny run. |
| T10-03 | Existing output, invalid section key/range, corrupt checkpoint/replay, missing input | Nonzero exit and actionable error. Existing artifacts are unchanged. No unsupported setting is silently ignored. |
| T10-04 | Offline workflow with a sentinel installed on GameController.connect/apply that raises if used | Every offline command succeeds without calling either entry point or loading a real controller backend. Include a fresh-process check so previously imported modules cannot hide a dependency. |
| T10-05 | Frozen policy, zero perturbation and each declared stress case | Zero perturbation reproduces ordinary evaluation. Every stress case records its applied settings, seeds, attempt count and failures. No NaN or unbounded episode; missing observations are flagged. Driving failures are recorded, not suppressed. |
| T10-06 | Recompute aggregate results from raw episode records | Counts, completion rates, successful-lap times and failure statistics agree. Checkpoint and split identities are traceable; no cherry-picked best lap replaces the full results. |

Run the two named files and the full available test suite once. Resolve new
failures. Preserve the existing UDP limitation as a separately identified failed
check unless it has been fixed and rerun; do not hide it behind a broad skip.

**Driving acceptance experiment:** use three independent training seeds and
20 whole held-out test layouts with two fixed valid starts each. Each initial
and selected trained checkpoint gets the same 40 test attempts; evaluate the
zero-action and follower baselines on those same conditions. Development uses
different whole routes. Freeze model selection, training budget, seeds, starts
and config before requesting any test results.

Initial project target, set here before testing: mean completion across the
three trained runs is at least 50%, and at least two of the three runs improve
by at least 10 percentage points over their own initial checkpoint and over the
zero-action baseline. Report per-run counts and spread. These are provisional
hobby-project acceptance targets, not promised performance or a statistical
guarantee. A change needs a recorded rationale before opening the final test
results; failures remain failures.

Use validation routes for a fixed stress matrix: nominal, start offset +/-1 m,
heading error +/-0.1 rad, grip multipliers 0.8/1.2, added delay 0.1 s, position
noise standard deviation 0.25 m, and a 0.2 s observation dropout. Run each factor
separately over at least 10 routes/two starts and record cases that are physically
invalid under the config before running. Stress results diagnose limits; they
have no invented required success percentage.

Inspect at least one completion and one failure replay (or a deliberately induced
failure if the suite has none). Software completion and the driving-quality gate
must be reported separately. Final test failures must lead to a recorded new
experiment; do not retune against those routes and keep calling them unseen.

## Handoff

A concise report with fresh-setup commands, configs, checkpoint identity, artifacts,
measured results and limitations. T2/T7/T8 are still required before game transfer.
