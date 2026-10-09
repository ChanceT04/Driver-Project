# Testing and ticket acceptance

The numbered acceptance cases in each ticket are required implementation work.
They are specifications today, not tests that already exist or have passed.
Implement the test files when implementing their ticket; do not create empty
test files or skip-marked placeholders to make the suite look complete.

## What a developer must deliver

1. Map each ticket case ID to an automated test or an explicitly named manual/
   experimental check. A related group of assertions may share one test.
2. Establish expected answers independently: hand-calculated geometry/dynamics,
   literal protocol fixtures from the source document, manually labelled images,
   or separately recorded episode outcomes. Do not generate both expected and
   actual answers with the same production helper.
3. Test normal behavior, the specified failure cases and the real public command
   path. Mock external devices/clocks for repeatable boundary tests; retain real
   integration runs for the behavior those mocks cannot prove.
4. Run focused tests and affected regressions. Record actual commands, test counts,
   exit codes and output. A command reporting zero discovered tests is a failed
   verification step. Do not count CLI help, file existence or stub imports as
   implemented feature evidence.
5. Save required demonstration artifacts in a new ignored runs/<name>/ directory.
   Inspect visual output where the ticket requires it. A generated image/video
   without an inspection record leaves that acceptance case pending.
6. Append the result to the assigned ticket and update its task-index status.
   Mark implemented/awaiting review only when required deterministic checks pass;
   explicitly identify any pending real-data, visual or learning-quality gate.

Do not fix a failing check by deleting it, weakening its assertion, hiding a
failure with a blanket skip, or changing its expected answer to match output.
If the specification itself is wrong, explain the independent evidence and
record a reviewed correction. Numerical tolerances and empirical targets must
be stated before scoring; do not quietly enlarge them after a failure.

## Running the checks

Run from the repository root with the project's selected Python interpreter:

```powershell
python -m unittest discover -s tests -p "test_track_*.py" -v
python -m unittest discover -s tests -p "test_training_framework.py" -v
python -m unittest discover -s tests -p "test_program_scaffold.py" -v
```

The first command is the future T1 example. Replace the pattern with the exact
test file/group named in your assigned ticket; confirm a nonzero discovery count.
The root README records the known interpreter path if the Windows python alias
is unavailable. Base tests use unittest; any new testing dependency must be
declared and justified with its command documented.

Run the full suite at T10 and when shared-interface changes create broad regression
risk:

```powershell
python -m unittest discover -s tests -v
```

The last scaffold run was 21/22 passing; the pre-existing UDP datagram test failed.
See [telemetry notes](telemetry.md). Record this failure by its exact test name
when present. Unrelated offline work can proceed with that limitation explicit;
T7 must investigate it. Never convert a failed test into a claimed pass or assume
the host is the cause without evidence.

## Regression scope

| Change | Recheck |
| --- | --- |
| T1 geometry/import | T1 tests; existing runner/scaffold tests |
| T4A simulator/replay | T1 tests, simulator/observation/replay checks, runner/scaffold |
| T3 generator | Geometry/import plus generator and CLI behavior |
| T4B dynamics/progress | Existing simulator, observation and replay checks plus variation cases |
| T5 observations/reward | Simulator/progress and runner/scaffold plus new observation/reward/metric cases |
| T6 learning/integration | Observation/reward/metrics, runner/scaffold and learning tests |
| T2 perception | Geometry plus synthetic and real-image acceptance |
| T7 recording | Existing telemetry tests, Session parser and synchronized capture checks |
| T8 live observations | Perception, common observations, calibration and timing checks |
| T9 controller | Fake-backend tests, offline-isolation regression, then authorized real-input checks |
| T10 integration | Complete installed/source workflows and full suite, plus declared learning experiment |

Stop repeating successful checks unless a new edit or unresolved failure warrants
it. Long training runs are acceptance experiments, not routine unit tests.
Keep quick deterministic tests practical for a local developer.

## Learning and real-world evidence

Keep three outcomes distinct: software behavior passes, learning improves the
driver, and the game adapter works with real inputs. None establishes the others.
Report completion counts and denominators, not only percentages or reward.
Use fixed evaluation conditions, whole-layout splits and fresh-process checkpoint
reload. Never choose test tracks after seeing which ones a policy completes.

T6 uses validation for iteration. T10 freezes its candidate/config and final test
suite before testing. Test-set reuse after tuning must be disclosed; future unseen
claims require new withheld layouts. The numerical learning/perception targets in
the tickets are initial project criteria, not measured results or guarantees.

Unavailable game access or ambiguous source images leave the corresponding real
evidence pending. Complete independent implementation/checks and identify the
specific missing evidence. Do not fabricate data or report synthetic checks as
real capture, calibration or control success.

## Handoff format

Append a concise record to the assigned ticket; lengthy logs can live in runs/:

| Case IDs | Result (pass/fail/pending/not applicable) | Evidence |
| --- | --- | --- |
| Assigned cases | Actual result, never a prefilled pass | Test names, command/exit code, counts, artifact path |

Include the interpreter/dependency versions, relevant seed/config/checkpoint IDs,
inspection notes, unresolved failures and any approved specification changes.
Not applicable requires a concrete reason (for example, an RL-only target test
when pure imitation was selected); it is not an escape from a difficult case.
Senior review checks the evidence before dependent work relies on it.
