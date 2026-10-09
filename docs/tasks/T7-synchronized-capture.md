# T7 — Synchronized, read-only HUD and UDP capture

Status: **planned; assign after T2 review**.

Implement the existing `telemetry/session.py` and `synchronized_capture.py`
entry points. Keep new raw same-session recordings under `data/captures/`;
analysis belongs in `runs/<name>/`. The offline simulator can progress independently.

## Objective

Produce evidence from the **same game session** so HUD pose/route, motion telemetry, and session metadata can be compared. The existing Melbourne video and Monza UDP files cannot provide this alignment.

## Work

- Add a read-only capture path that timestamps screen frames and UDP datagrams on one monotonic clock, with recording metadata (resolution, HUD layout, selected UDP format, track/session identity when available). Do not block or slow UDP reception to process images.
- Decode the limited 2026 Session packet fields needed here—track ID, track length, session type—against EA's 2026 structure linked in `docs/telemetry.md`. Check packet length, offsets, signedness, and version; preserve current decoders.
- Save raw frames or a lossless/replayable visual stream and raw UDP separately, with a small index linking local timestamps. Keep recordings local and never overwrite an existing capture.
- Specify a short user-run offline recording procedure with the large full map and ghost disabled. The developer must not change game settings or control the car as part of this ticket.

## Acceptance evidence

- Synthetic packet-offset tests plus a read-only metadata check on both existing raw captures. Report the observed values, including any format/version mismatch.
- A real same-session capture demonstrates frame/UDP timestamps, dropped-frame counts, parse failures, and the time range shared by both streams. If a real run is unavailable, report that limitation; do not call the timing verified.
- Investigate the existing UDP datagram-capture test failure recorded in
  `docs/telemetry.md`; establish whether it is code, timing or host-related before
  claiming the capture checks pass. Preserve evidence of any execution limitation.

## Out of scope

Policy inference, metric map calibration, and game input.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Implement
`tests/test_session_metadata.py` and `tests/test_synchronized_capture.py`;
retain the existing telemetry regression tests.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T7-01 | Synthetic Session packet encoded from independently cited EA field offsets/lengths, including track_id=-1 and a normal track | Exact track ID, track length and session type; correct signedness. Tests do not import decoder offset constants to construct their expected packet. Wrong length/format/version is rejected. |
| T7-02 | Replay both preserved raw captures read-only | Report actual Session packet counts and decoded values, or explicit absent/unsupported status. Never invent metadata for a capture with no valid Session packet. Capture hashes before/after are identical. |
| T7-03 | Fake clock/screen/UDP sources with known capture-start/end and arrival times | Every recorded event uses the same monotonic clock domain; acquisition time/interval remains distinguishable from later write time. Preserve byte-identical UDP payloads and original event timestamps. |
| T7-04 | Deliberately blocked image processing while feeding 100 fake UDP packets into the receive/queue boundary; force frame-queue overflow | UDP receive path records all 100 injected packets independently. Frame loss is counted accurately; no unbounded queue growth or fabricated frames. This fake-source check is separate from real socket delivery. |
| T7-05 | Stop during capture, empty capture, disk-write error, existing directory | Clean stop flushes readable metadata/index and closes resources. Write failure is reported; partial capture is labelled incomplete. Existing captures are never overwritten. |
| T7-06 | Missing/out-of-order events and separate session identities in replay | Drop/gap information is preserved. Records from different sessions are never silently joined; timing diagnostics expose discontinuities. |

Run both new test files plus `test_telemetry.py`. Investigate the documented
zero-datagram socket-test failure; synchronize receiver readiness in the test
if appropriate instead of masking it with arbitrary sleeps or broad skips.

Real-input gate: a user-run capture of at least 30 seconds with overlapping screen
and UDP coverage. Report frame/packet counts, both drop counts, common time span,
interval distributions and malformed records. Playback must align manually chosen
straight and turning events using recorded timing; common-clock timestamps alone
do not establish visual/telemetry sensor synchronization. If game recording is
unavailable, mark the real-input gate pending and preserve synthetic test results.
