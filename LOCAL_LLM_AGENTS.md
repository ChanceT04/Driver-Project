# Local developer handoff

For the high-level pickup and completion workflow, start with
[START_HERE.md](START_HERE.md). This file adds local implementation conventions.

Act as the implementing developer for the explicitly assigned ticket. Codex acts
as senior engineer and reviewer. The goal is a working offline simulator that
trains a driver across varied tracks, followed by separately tested game integration.

## Where to work

Current repository root:
`C:\Users\Chance Larson\Documents\Codex\2026-10-08\i-x20\outputs\f1-25-racing-agent`

Remote: https://github.com/ChanceT04/Driver-Project.git

Resolve all task paths from this root. If it is missing, report that exact problem;
do not scan the machine for another clone. This dated workspace is the current
location, not a permanent convention.

## Read before implementing

1. AGENTS.md and this file.
2. [Task index](docs/tasks/README.md) and your assigned ticket.
3. [Architecture](docs/architecture.md) and the ticket's existing modules.
4. [Testing and acceptance](docs/testing.md) and the ticket's numbered test cases.

The offline order is T1 -> T4A -> T3 -> T4B -> T5 -> T6 -> T10.
T3 can run after T1 independently of T4A. T2 is a separate perception branch and
does not block simulator training. Preserve these IDs in reports.

## Complete the assigned unit

The repository has real telemetry/runner code plus explicit interface scaffolding.
A function raising NotImplementedError is unfinished. Fill the assigned functions,
connect the relevant CLI path, validate your config section and demonstrate its
actual behavior. Do not replace useful interfaces with disconnected scripts or
claim completion because files exist.

Your assignment authorizes routine implementation and listed tests/experiments
within that ticket. Do not repeatedly ask for permission to carry it out.
Do not expand into later tickets without assignment. Flag a blocking interface
problem with a concrete proposed correction; coordinate edits across its callers.

Explicit authorization to choose the next task counts as an assignment: select
one eligible unclaimed ticket through the task index and record the choice.

Use Python 3.10+ and declare new dependencies in pyproject.toml. Source-checkout
commands use scripts/sim.py; optional installation exposes f1-sim. The root README
records the known local interpreter fallback. Keep generated output under a new
runs/<name>/ directory; never overwrite captures or prior results.

## Evidence and handoff

The assigned ticket's numbered acceptance cases are mandatory. Implement their
tests with the feature, record independent expected values, and map every case ID
to evidence. Run the named focused commands and affected regressions; zero tests
discovered is not a pass. Report visual/real-data/learning gates separately from
unit tests. Do not weaken expected results or silently skip failures to finish.

- Add meaningful tests for implemented behavior. Import/help/stub checks are scaffold
  evidence only. Synthetic data does not prove real HUD extraction or UDP offsets.
- Use consistent units, frames, signs, clocks and schema versions.
- Record exact checks, exit codes, actual measured results and artifact paths.
- Update the task-index status and append a concise handoff to the assigned ticket.
  State limitations and what the next task can now use.
- Keep work uncommitted for review unless the user asks for a commit.

Preserve telemetry, screenshots and user work. Do not reset/clean Git or change
history. Game-input trials require T9 assignment and explicit input authorization.
Importing or running the offline trainer must never connect to a game controller.
