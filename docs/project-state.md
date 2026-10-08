# Project state

Last updated: 2026-10-08

## Goal

Build an autonomous driver for private, offline F1 25 sessions. Start with one circuit and telemetry-based observations; ultimately achieve repeatable valid laps faster than the human baseline.

## Current phase

Phase 0 (project setup) is complete. Next: Phase 1, a read-only telemetry feasibility receiver and recorder. No game-control code or measurements exist yet.

## Confirmed context

- F1 25 is installed.
- User-reported development hardware: Radeon RX 9070 XT, Ryzen 5 5600, 32 GB DDR4 RAM. Operating system and driver versions still need confirmation before choosing a training runtime.
- User prefers telemetry-based driving, provided the observed update/control timing is suitable.
- The first learning target is one track. The human lap is guidance and a benchmark; the driver should be allowed to improve beyond it.
- ChatGPT Work is intended for architecture and direction; the user's local gpt-oss 20b is intended for bounded implementation practice.
- GitHub repository: https://github.com/ChanceT04/Driver-Project (public).

## Decisions already made

- Keep initial telemetry capture read-only.
- Separate telemetry, track mapping, control, simulation, policy/training, and evaluation.
- Keep raw telemetry, generated runs, and checkpoints out of Git.
- Decide the training route after measuring telemetry timing, map suitability, game-control response, and restart cost.

See `docs/decisions/README.md` for decision records and `docs/experiment-log.md` for measured results.

## Open questions

- Which circuit will be the first benchmark?
- What OS, graphics driver, and Python runtime are installed?
- What packet cadence, arrival jitter, loss rate, and usable fields does the game provide on this machine?
- Which repeatable offline session and restart procedure will be used?
- Is an existing map accurate enough, or should we record one from telemetry?
- Does a fast simplified simulator justify its setup and transfer risk?

## Next task

Implement a small Python UDP receiver that validates the selected F1 25 packet format, records game and local monotonic timestamps, and saves a read-only capture. During a short offline drive, measure packet cadence and gaps and verify that world-position samples trace a recognizable lap. Do not send game input.
