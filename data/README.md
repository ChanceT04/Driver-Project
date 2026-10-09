# Local data inventory

Preserve these inputs. They remain useful alongside procedural simulator training.

| Location | Contents and intended use |
| --- | --- |
| telemetry/raw/first-session.jsonl | Original UDP capture; read-only replay/decoder evidence |
| telemetry/raw/second-session.jsonl | Original UDP capture; contains the usable Monza lap |
| telemetry/processed/second-session-valid-lap.jsonl | Existing derived human driving examples |
| maps/reference/ | Three original full-resolution in-game screenshots for T2 |
| captures/ | Future same-session screen/UDP recordings produced by T7 (ignored) |

The Monza export contains 4,966 samples from one valid 82.741-second lap.
It is demonstration evidence, not an unseen-track evaluation set.
See [telemetry notes](../docs/telemetry.md) for recording and export commands.

The external Melbourne clip is at
`C:/Users/Chance Larson/Videos/Radeon ReLive/F1 25/F1 25_2026.10.08-19.56_1.mp4`.
It is not synchronized with the Monza captures.

Generated route previews, temporary extractions, replays and learned models go
under runs/<name>/ rather than beside original inputs. Small synthetic geometry
fixtures belong under tests/fixtures/tracks/. Large captures and training outputs
stay ignored by Git.
