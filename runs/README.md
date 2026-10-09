# Local experiment output

Use one new directory per run: runs/<name>/.

All run outputs are ignored by Git. Keep configuration examples in configs/ and
small reproducible fixtures in tests/fixtures/. Each actual training run will
contain resolved settings, episode results, checkpoints and selected replays.
See [architecture](../docs/architecture.md) for the artifact contract.

The simulator/trainer is not implemented yet; this folder contains no claimed
trained model. Never overwrite an existing run to reuse its name.
