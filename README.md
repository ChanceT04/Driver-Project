# F1 25 Racing Agent

An offline, single-player autonomous driving research project for F1 25. The first milestone is a telemetry-only recorder and feasibility study; automated control and machine learning come later.

## Current scope

- One circuit, fixed car and setup, dry conditions, and Time Trial or another repeatable offline mode.
- Read the game's documented UDP telemetry and record it with local receive timestamps.
- Validate a track map against recorded world positions.
- Keep telemetry reading, controller input, simulation, and learning as separate modules.
- Optimize valid lap time after establishing a repeatable human baseline.

## Project map

See [architecture](docs/architecture.md) and [roadmap](docs/roadmap.md). `AGENTS.md` contains coding-agent instructions.

## Safety of experiments

Initial tools are read-only. Do not send controller input, edit game files, join multiplayer, or submit leaderboard laps until the control phase is explicitly designed and reviewed. Raw telemetry and model checkpoints stay local and are excluded from Git by default.

