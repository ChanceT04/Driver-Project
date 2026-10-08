# Instructions for coding agents

- Read `docs/architecture.md` and `docs/roadmap.md` before changing project structure.
- Work only on the specifically assigned module. Preserve the documented module boundaries.
- Keep the initial telemetry receiver read-only: never send game input or alter game configuration automatically.
- Prefer small Python modules with typed interfaces and clear units for every measurement.
- Parse only the official F1 25 UDP format selected by configuration; validate packet format, version, length, and player-car index before decoding.
- Log both game timestamps/frame identifiers and local monotonic receive times. Do not silently hide missing or stale packets.
- Do not invent telemetry fields or assume map coordinate axes; verify against recorded data and document conventions.
- Never commit raw telemetry, personal data, checkpoints, local settings, or secrets. Keep generated run artifacts under ignored `data/` or `runs/` paths.
- Do not add automated controller behavior until the user has reviewed the control design and restart behavior.
- When assigned an implementation, state what files changed and how the behavior was checked. Do not widen scope without asking.
