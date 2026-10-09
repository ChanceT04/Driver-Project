# Agent start guide

You are implementing an assigned piece of an F1 driving-agent project. Our first
milestone is a working offline simulator that trains a driver on varied tracks
and evaluates it on unfamiliar ones. Game integration follows later.

## 1. Locate the project and your assignment

Work from this repository's root. The current absolute location is recorded in
[AGENTS.md](AGENTS.md#repository-location). Resolve ticket paths relative to that
root; do not scan the machine for another checkout if this one is unavailable.

Read [AGENTS.md](AGENTS.md) and [local developer instructions](LOCAL_LLM_AGENTS.md).
Inspect the current files and Git status before editing so you can preserve
existing user work.

Open the [task index](docs/tasks/README.md). Find the ticket ID supplied in your
assignment and follow its link to the full ticket. For example, an assignment
of T1 leads to [T1 — Track contract and importer](docs/tasks/T1-track-contract-importer.md).
Do not guess a filename from the ticket number: T4 has separate T4A and T4B tickets.

Check the ticket's prerequisites and any previous handoff notes. Work on the
assigned ticket only. If explicitly told to pick the next task, use the index's
dependency order and choose an unclaimed task whose prerequisites are reviewed.
If no task or task-selection instruction was supplied, ask for the assignment.
If prerequisites are missing, report the precise gap and continue only independent
work within your assigned scope; do not mark a prerequisite complete yourself.

## 2. Understand what you must deliver

Read the whole ticket, including its numbered acceptance tests. Then read the
[architecture](docs/architecture.md), [testing requirements](docs/testing.md),
and the existing modules owned by that ticket. Use the index's code-ownership
table to locate them. Read other documents only when relevant to the assignment.

The repository contains both working code and unfinished interfaces. A function
raising NotImplementedError is a starting point for implementation. Your job is
to implement the ticket's behavior, connect its public command where required,
and demonstrate it with the prescribed tests and artifacts.

Before editing, briefly state the ticket, intended deliverable and checks you
will run. Mark its row and ticket status In progress, identifying your agent/task
and date. If it is already claimed by another active developer, resolve ownership
with the coordinator before overlapping edits.

## 3. Implement and verify

- Use the existing interfaces and keep changes within the assigned unit. Make
  routine implementation decisions without repeatedly asking for permission.
- Implement the required tests alongside the feature. Use independent expected
  answers; follow the ticket's exact inputs, edge cases and tolerances.
- Connect configuration and CLI behavior where the ticket requires it. Declare
  any justified new dependencies in pyproject.toml.
- Run the named checks and affected regressions. Record commands, exit codes,
  test counts and actual results. Zero discovered tests is not a pass.
- Save generated evidence in a new runs/<name>/ directory. Preserve original
  telemetry, screenshots, existing runs and unrelated changes.
- Inspect required replays/overlays. Keep failed attempts in experimental reports.
  Report software correctness, learning improvement and real-game evidence
  separately. Missing real data or unavailable tools leave those checks pending.

The root [README](README.md#run-from-this-checkout) contains setup, command entry
points and the known local Python fallback. Unfinished-command errors are not
successful feature runs. The testing guide records the known UDP test failure;
do not hide it or claim the full suite passed if it remains.

If a shared contract must change, explain why and coordinate its affected callers.
If blocked, document the exact blocker, attempted checks and smallest next action.
Do not fill gaps with invented data or weaken an acceptance test to obtain a pass.

## 4. Finish with a reviewable handoff

Review your changes for accidental edits and remaining unfinished behavior in the
assigned scope. Update only the relevant ticket/index entries and documentation
whose usage actually changed.

Append a dated Implementation handoff section to the ticket containing:

1. Ticket ID, implementing agent/task, and outcome.
2. Implemented behavior and changed files, distinguishing your changes from
   pre-existing work.
3. Each acceptance-case ID mapped to pass, fail, pending or justified not applicable.
4. Exact test/demo commands, exit codes, counts and relevant measured results.
5. Artifact paths and configuration/seed/checkpoint identities where applicable.
6. Remaining limitations or blockers, and what dependent work can now use.

Use these statuses consistently in both the ticket and task index:

| State | When to use it |
| --- | --- |
| In progress | You are actively implementing the assigned unit. |
| Blocked | A specific dependency, tool or missing input prevents further required work; include the reason. |
| Implemented — evidence pending | Code and available checks are done, but a required real-data, visual or experimental gate remains. Name it. |
| Implemented — awaiting review | Required checks and evidence are complete; the senior reviewer still needs to assess them. |
| Reviewed / complete | Set by the reviewer after acceptance, unless your assignment explicitly includes that authority. |

Send the user/coordinator a concise final report with the ticket, result, test
evidence, handoff/artifact locations and any unresolved issue. Keep work
uncommitted unless the user requested a commit. Do not reset/clean Git, push,
start the next ticket or claim review approval on your own.

An assignment covers routine implementation and its listed checks. Real game
inputs additionally require explicit authorization under T9. Offline development
must never connect to a game controller.
