# F1 driving agent

Train a driver that can complete a cautious lap on an unfamiliar circuit. First,
build a fast offline 2D simulator that generates varied tracks and trains a
policy on car-relative route previews. Later, provide the same observations
from F1's full HUD map, player triangle and UDP telemetry.

## Start here

- **Agents picking up work: read [START_HERE.md](START_HERE.md) first.**
- [Task index and implementation order](docs/tasks/README.md) — the authoritative work queue.
- [Architecture and shared contracts](docs/architecture.md) — how the program fits together.
- [Local developer instructions](LOCAL_LLM_AGENTS.md) — how to complete an assigned ticket.
- [Training framework](docs/training-framework.md) — what the existing runner actually does.
- [Testing and acceptance](docs/testing.md) — required ticket checks and evidence.
- [Telemetry](docs/telemetry.md) and [local data inventory](data/README.md).

## What exists today

| State | Components |
| --- | --- |
| Implemented | T1 route geometry and JSON importer, synthetic oval fixture, UDP capture/decoding/reporting, valid-lap dataset export, generic episode/experiment runner |
| Implemented prototype | T4A fixed-route 2D simulator, v1 driving observation, diagnostic route follower, episode recording and HTML replay; visual review pending |
| Implemented scaffolding | Package metadata, offline CLI routing/help, shared config-envelope validation, zero-action baseline |
| Interfaces awaiting implementation | Procedural tracks, T4B response/grip limits, final reward/metrics, learned policy/training assembly, HUD and game adapters |

**There is no trained driver or real-game control path yet.** The T4A simulator
is a fixed-route learning prototype, not a calibrated F1 physics model. Passing
its offline checks does not prove learning, perception or game control.

## Run from this checkout

Python 3.10+ is sufficient for existing code. The current base package has no
third-party runtime dependencies. The assigned feature owner adds justified
rendering, vision or ML dependencies to `pyproject.toml`.

```powershell
python scripts/sim.py --help
python scripts/sim.py check-config --config configs/offline.example.json
python -m unittest discover -s tests -v
```

If this PC's `python` alias is unavailable, the interpreter previously used here is:

```powershell
& 'C:\Users\Chance Larson\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/sim.py --help
```

Optional installation in your own Python environment: `python -m pip install -e .`.
That exposes `f1-sim` and `f1-telemetry`; source-tree scripts work without installation.

## Intended complete-program workflow

These command routes exist, but the feature commands currently stop with an
explicit unfinished-ticket message. Only help and shared config checks work now.

```powershell
python scripts/sim.py preview-tracks --config configs/offline.example.json --output runs/track-preview
python scripts/sim.py simulate --config configs/offline.example.json --route tests/fixtures/tracks/oval.json --output runs/first-drive
python scripts/sim.py train --config configs/offline.example.json --output runs/first-training
python scripts/sim.py evaluate --config configs/offline.example.json --checkpoint runs/first-training/policy --split validation --output runs/policy-evaluation
python scripts/sim.py replay runs/first-drive/episode.jsonl --output runs/first-drive/replay.html
```

T1 creates the oval fixture. T4B enables `simulate` without `--route`. T6
defines and documents the checkpoint format. T10 supplies a measured training
config: the current example is a draft, with `agent.method: null`, and cannot
be presented as a proven training recipe.

## Directory map

```text
configs/                 small checked-in experiment configurations
data/                    preserved telemetry, reference images, later synchronized captures
docs/architecture.md     shared program and data contracts
docs/tasks/              task index and bounded developer tickets
scripts/                 source-checkout command entry points
src/f1_agent/
  track/                 route geometry, JSON import, procedural generation
  environment/           car dynamics, episodes, reward, diagnostic run and replay
  evaluation/            common observations, metrics and robustness experiments
  policy/                diagnostic baselines and learned agent/checkpoints
  training/              configuration, runner, training assembly, human-lap export
  perception/            full HUD route and player triangle extraction
  telemetry/             UDP tools and later synchronized screen capture
  runtime/               later read-only live observation adapter
  control/               later explicitly authorized game-input adapter
tests/                   checks and small synthetic fixtures
runs/                    ignored per-experiment results, replays and checkpoints
```

Simulator completion is the immediate milestone. Transfer to F1 follows
separate capture, calibration and supervised-control tickets. No ticket is
complete solely because its module imports or its command prints help.
