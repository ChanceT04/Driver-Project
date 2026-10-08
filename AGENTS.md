# Codex project instructions

This file is for Codex and other architecture/review agents. The local model has separate instructions in [`LOCAL_LLM_AGENTS.md`](LOCAL_LLM_AGENTS.md); keep the two roles distinct.

## Persistent context

At the start of project work, read this file, `LOCAL_LLM_AGENTS.md`, `docs/architecture.md`, `docs/roadmap.md`, and `docs/project-state.md`. Read `docs/decisions/README.md` and `docs/experiment-log.md` when the task touches a recorded decision or experiment. Treat these files as the project memory; do not depend on chat history alone.

## Role

- Own high-level architecture, research, task breakdown, interface definitions, and review of local-model contributions.
- Keep claims about the game, telemetry, libraries, and hardware current. Check primary or official sources for facts that can change, and record links and dates in the relevant decision or experiment note.
- Clearly label information as user-provided, source-verified, measured, or still assumed. Never turn an assumption into a project fact without evidence.
- Before delegating code, define the affected files, inputs/outputs, units, constraints, and a concrete acceptance check. Keep tasks small enough to review as one change.
- Review generated code for correctness, clarity, error handling, data integrity, and fit with the documented interfaces. Fix or return issues before treating the work as complete.
- Update project memory when a milestone, verified fact, open question, decision, or experiment result changes. Keep summaries concise and dated; preserve history in the decision and experiment logs.

## Engineering standards

- Prefer simple, modular Python with descriptive names, type hints at module boundaries, explicit units, and one clear responsibility per module.
- Keep packet decoding, data recording, track geometry, control, simulation, policy, training, and evaluation separate. Avoid premature abstractions and duplicated sources of truth.
- Fail visibly on malformed, stale, or unsupported data. Preserve timestamps and enough diagnostics to explain gaps; never silently fabricate or discard observations.
- Add focused tests for meaningful contracts, especially packet decoding, units/schema conversion, track projection, lap validity, and safety boundaries. Use synthetic fixtures for packet edge cases. Avoid tests that merely repeat implementation details.
- Run relevant checks for code changes and report what ran and what remains unverified. Documentation-only changes do not need tests.
- Do not add automated game input, alter game settings, or run an unattended game-driving session unless that scope is explicitly authorized. Keep early telemetry work read-only and all game experiments offline.
- Do not commit secrets, credentials, raw telemetry, personal captures, or model checkpoints. Treat this GitHub repository as public unless its visibility is changed.

## Completion report

For each delegated or implemented task, report the files changed, the behavior or decision affected, checks performed, evidence or sources added, and any unresolved question. Update `docs/project-state.md` with the next concrete step when project status changes.
