# Local LLM coding instructions

This file is specifically for the user's local gpt-oss 20b coding model. Codex's separate instructions are in [`AGENTS.md`](AGENTS.md). The user should provide this file and the assigned task to the local model; it may not load repository guidance automatically.

## Read first

Before coding, read `AGENTS.md`, `docs/architecture.md`, `docs/roadmap.md`, and `docs/project-state.md`. Read the relevant decision or experiment record if the task refers to one. If any required context or interface is missing, state the gap and ask for a narrow clarification rather than guessing.

## Your role

- Implement the bounded task the user or Codex assigned. Do not redesign architecture, select a new learning method, change scope, or edit unrelated modules.
- Follow the exact file scope, interface, data units, and acceptance checks in the task. If an improvement requires changing those, explain the proposal separately and wait for direction.
- Write clean, straightforward Python: meaningful names, small functions, explicit units, type hints at boundaries, useful errors, and comments that explain intent rather than restate code.
- Keep modules focused. Do not add dependencies, configuration knobs, fallback behavior, or abstractions without a stated need.
- Do not invent packet fields, coordinate conventions, measurements, or API behavior. Mark uncertainty and surface it to the reviewer.
- Preserve raw evidence and timestamps. Never silently coerce malformed data into plausible values.

## Safety and data handling

- The initial telemetry receiver is read-only. Do not send controller input, edit game configuration, launch or control F1 25, join multiplayer, or submit leaderboard laps.
- Never add credentials, user identifiers beyond what the task needs, raw telemetry, screenshots, personal captures, or model weights to Git. Generated data belongs in the ignored `data/` or `runs/` folders.
- Assume the GitHub repository is public. Keep committed content appropriate for public viewing.

## Verification and handoff

- Add or update focused tests for meaningful behavior, especially binary packet parsing, malformed/truncated packets, player-car selection, timestamps, and lap-validity rules. Do not write tests that only restate the code.
- Run only checks relevant to your change. If a check cannot run, say so plainly; never claim success without output or evidence.
- Before handing off, summarize: changed files, implementation choices, commands/checks run, known limitations, and anything that needs Codex review. Do not edit `docs/project-state.md`, decisions, or roadmap unless explicitly assigned; instead report facts that need recording.
