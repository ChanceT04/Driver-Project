# Telemetry tool

This is a read-only recorder and offline analyzer for the game's **2026 UDP mode**. The user's settings are UDP on, broadcast off, `127.0.0.1:20777`, 60 Hz, 2026 format, Your Telemetry Restricted, and player names off. Two Monza captures confirmed supported packet arrival at about 60 Hz with no malformed datagrams. The configured send rate remains distinct from the measured receive rate.

## Run

Use a Python 3.10+ interpreter. From the repository root, start the recorder **before** entering an offline driving session:

```powershell
python scripts/telemetry.py capture data/telemetry/raw/first-session.jsonl
```

Press Ctrl+C to finish and close the file. The recorder creates a new file and refuses to overwrite an existing capture. It listens only on `127.0.0.1:20777` by default. For a bounded trial, add `--duration 30` or `--max-packets 1000`. On this PC, the `python` command currently points to an unavailable Windows alias. The tested interpreter can be used instead:

```powershell
& 'C:\Users\Chance Larson\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/telemetry.py capture data/telemetry/raw/first-session.jsonl
```

After recording:

```powershell
python scripts/telemetry.py report data/telemetry/raw/first-session.jsonl
```

Captures under `data/telemetry/raw/` are ignored by Git. A capture can still contain session identifiers and other game data; inspect it before sharing. The recorder does not inspect packets on the receive path. Each JSONL file starts with capture metadata, then one record per datagram containing a local monotonic arrival timestamp, sender address, and the full datagram as base64. This is a lossless byte representation, not decoded telemetry. Session time and frame IDs are decoded separately during replay.


To create an offline observation/action dataset from fully aligned valid completed laps:

```powershell
& 'C:\Users\Chance Larson\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/build_dataset.py data/telemetry/raw/second-session.jsonl data/telemetry/processed/second-session-valid-lap.jsonl
```

The output is a local-only JSONL file. It contains a metadata record and one sample per frame with Motion/Lap/Car Telemetry observations and recorded steering, throttle, and brake. The exporter refuses to overwrite output and excludes partial, invalid, unaligned, or malformed laps. This is demonstration data for offline experiments; it does not train a policy or prove the policy can control the game. The captured Monza example contains 4,966 samples from one valid 82.741-second lap.

## Source and verification

The parser uses EA's [2026 Season Pack telemetry structures](https://forums.ea.com/t5/s/tghpe58374/attachments/tghpe58374/f1-games-game-info-hub-en/61/8/2026%20Season%20Pack%20Telemetry%20Output%20Structures%20(1).txt): a 29-byte header, 24 car slots, and exact Motion/Lap/Car Telemetry packet lengths of 1325/1399/1448 bytes. Synthetic tests encode literal lengths and field offsets from this source and exercise a nonzero player index, the last index, signed values, bad lengths, wrong format, unknown IDs, raw-byte capture, and report behavior.

Run the checks from the repository root:

```powershell
python -m unittest discover -s tests -v
```

The live captures confirm actual headers, packet versions and lengths, plausible player fields, and observed timing. If a later game update emits a different version, preserve the capture and revise the parser against that evidence rather than assuming the synthetic tests are sufficient.

## Current local test limitation

During the scaffold reorganization on 2026-10-08, the full suite ran 22 tests;
21 passed. The pre-existing
`test_udp_capture_preserves_arbitrary_datagrams_and_shuts_down` failed because
the receiver recorded zero datagrams where the test expected two. The same
failure was observed before this reorganization. The recorder and decoder were
not changed by this work, and the cause has not been established. Do not report
the full suite as passing or attribute this to a host/network restriction without
investigating. T7 should revisit it before claiming synchronized capture works.
