# Roadmap

## Phase 0 — Project setup

Architecture and role instructions are recorded, the GitHub repository is connected, and project memory templates are in place. No game automation yet. Runtime conventions will be selected with the telemetry receiver task.

Exit condition: shared project memory and boundaries are established. Complete.

## Phase 1 — Telemetry feasibility (read-only)

Build a UDP receiver for the selected F1 25 format. Log selected player-car motion, car telemetry, lap data, session/frame identifiers, and local monotonic receive times. Drive several offline laps and report actual packet cadence, gaps, parse failures, and field plausibility.

Exit condition: a capture decodes consistently and its sampled world positions form a recognizable lap.

## Phase 2 — Track and baseline

Choose one circuit. Inspect community map coverage or record a map from additional telemetry laps. Validate coordinate alignment and track limits in a viewer. Record multiple clean human laps under fixed conditions.

Exit condition: map alignment is credible and the baseline includes lap/sector times and invalid-lap rules.

## Phase 3 — Control feasibility

Separately test an input adapter with conservative, supervised, offline actions. Measure action delay, applied-control behavior, and restart/recovery reliability. Keep a hard stop path.

Exit condition: repeatable safe control and reset behavior are demonstrated.

## Phase 4 — Baseline driver and learning route

Build a conservative path-following/speed-control baseline. Compare direct game attempts with a small simulation informed by measured game response. Decide whether simulation pretraining is worth its transfer risk and setup cost.

Exit condition: stable benchmark and selected training path.

## Phase 5 — Learning and improvement

Train a continuous-action policy with staged guidance and progressively more freedom. Evaluate saved checkpoints with exploration disabled. Optimize valid-lap rate, consistency, then lap time against the human baseline.

Exit condition: repeatable autonomous valid laps; subsequent performance milestones are measured against the baseline.

## Phase 6 — Autonomous batches and expansion

Automate attempts, recovery, checkpointing, and reporting for private offline sessions. Add tracks, conditions, opponents, or race strategy only after the one-track benchmark is reliable.
