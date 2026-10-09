# T1 — Track contract and JSON importer

Status: Reviewed / complete. Dependencies: none.

## Deliver

Implement `track/geometry.py` and `track/json_io.py` using the public interfaces
already present. Supply a tiny synthetic oval at `tests/fixtures/tracks/oval.json`
for the first driving loop. No screenshots or video processing are needed here.

- Validate finite ordered closed loops and explicit coordinate frames.
- Fix the schema-v1 JSON fields for frame, points, closed status, source, width
  and width provenance. Normalize a repeated endpoint without double counting.
- Reject empty/degenerate geometry and inconsistent width metadata.
- Implement arc length, wrapped sampling, tangent and nearest projection.
  Define deterministic tie behavior and the optional previous-progress hint.
- Respect the axis and sign conventions in the architecture document.
- Read/write explicit versions; refuse to overwrite existing output.

## Evidence

Focused tests cover straight/bend projection, wraparound, repeated endpoint,
reversed travel direction, HUD y-axis sign, invalid values and JSON round trip.
The oval loads and can be sampled by the next developer. Document the public API
and fixture units. No arbitrary conversion from pixels to metres.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Implement
`tests/test_track_geometry.py` and `tests/test_track_json_io.py`.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T1-01 | Metre square ordered (0,0), (10,0), (10,10), (0,10), explicitly closed | Length 40; sample(5)=(5,0), sample(15)=(10,5), sample(40)=(0,0), sample(45)=(5,0), sample(-5)=(0,5), each within 1e-8. |
| T1-02 | Project (4,2) onto that square | Point (4,0), distance_along 4, lateral_offset +2 and tangent 0; within 1e-8. Compute these expected answers independently of the route helper. |
| T1-03 | Reverse the square to (0,0), (0,10), (10,10), (10,0); project (4,2) again | Point stays (4,0), distance_along becomes 36, lateral_offset becomes -2, tangent is equivalent to pi modulo 2*pi. For the original square in HUD pixels, the same projection has lateral_offset -2 because y points down. |
| T1-04 | Repeated closing endpoint; equivalent route without duplicate; vertex tie; nearby route branches with a previous-progress hint | Duplicated closure adds no length or zero-length segment. Both forms sample identically. Vertex/branch behavior is deterministic and matches the documented tie/hint rule. |
| T1-05 | Empty/two-point/zero-length loop, nonfinite coordinate, unknown frame, nonpositive width, width provenance contradicting missing width, unsupported JSON version | Clear validation failure. No partial output; no inferred pixel-to-metre conversion. |
| T1-06 | Save/load the square and oval; attempt writing onto an existing sentinel file | Geometry, travel order, frame and provenance survive round trip. Existing file bytes remain unchanged after the overwrite attempt. |

Run:
`python -m unittest discover -s tests -p "test_track_*.py" -v`.

Pass gate: all cases above pass, and the checked-in synthetic oval loads through
the public importer. Include its measured length and five sampled coordinates
in the handoff. This ticket does not need a renderer or a real-track screenshot.

## Handoff

Update the task index and report exact tests plus schema choices. T4A and T3
must be able to use this route representation without redesigning it.

## Implementation handoff — 2026-10-08

1. **Ticket / outcome:** T1, implemented by `/root`; ready for senior review.
2. **Behavior and files:** Implemented route validation, normalized repeated
   closure, wrapped arc sampling, outgoing-segment tangents, nearest projection,
   HUD-aware lateral signs and exact-distance tie resolution with optional
   wrapped progress hints. Added strict schema-v1 JSON load/save with exclusive
   create semantics, plus the documented API and synthetic octagonal oval.
   Changed for T1: `src/f1_agent/track/geometry.py`,
   `src/f1_agent/track/json_io.py`, `tests/test_track_geometry.py`,
   `tests/test_track_json_io.py`, `tests/fixtures/tracks/oval.json`, and
   `tests/fixtures/tracks/README.md`. Other pre-existing work in the checkout
   was preserved.
3. **Acceptance cases:**

   | Case | Result | Evidence |
   | --- | --- | --- |
   | T1-01 | Pass | `test_t1_01_square_length_and_wrapped_samples`; 40 m and all five prescribed samples within 1e-8. |
   | T1-02 | Pass | `test_t1_02_projection_and_left_offset`; independent expected projection `(4,0)`, progress 4, offset +2, tangent 0. |
   | T1-03 | Pass | `test_t1_03_reverse_direction_and_hud_sign`; reverse progress 36, offset -2, tangent pi modulo 2*pi, HUD offset -2. |
   | T1-04 | Pass | `test_t1_04_duplicate_endpoint_vertex_and_progress_hint`; closure normalization, samples, lowest-index vertex tie and hint-selected progress 17. |
   | T1-05 | Pass | `test_t1_05_invalid_route_geometry_and_metadata`, `test_t1_05_reject_unclosed_and_nonfinite_json`, and `test_t1_05_reject_unsupported_version_and_malformed_metadata`; invalid/degenerate inputs reject with `ValueError`. |
   | T1-06 | Pass | `test_t1_06_square_and_oval_round_trip_and_no_overwrite`; point order, frames and width provenance round-trip, sentinel bytes unchanged. The public oval importer check also passed. |

4. **Checks and measured results:** Python 3.12.14. The documented Windows
   `python` alias was unavailable, so checks used the README's local interpreter.
   The focused command
   `& 'C:\Users\Chance Larson\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -p "test_track_*.py" -v`
   exited 0, 8 tests passed. The regression command
   `& 'C:\Users\Chance Larson\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -p "test_training_framework.py" -v`
   exited 0, 6 tests passed. The regression command
   `& 'C:\Users\Chance Larson\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -p "test_program_scaffold.py" -v`
   exited 0, 4 tests passed. `git diff --check` exited 0 (only existing
   line-ending warnings for other modified files). The oval was loaded through
   `load_route`: measured length **116.5685424949 m**; samples: `s=0 ->
   (0,0)`, `s=10 -> (10,0)`, `s=30 -> (27.0710678119,7.0710678119)`, `s=60 ->
   (18.2842712475,30)`, and `s=100 -> (-10,12.4264068712)`. No generated run
   artifact was needed; the checked-in fixture is the evidence.
5. **Limitations / next use:** No pixel-to-metre conversion is inferred. This
   ticket does not test rendering, simulation, learned driving or real game
   data. T4A can load the fixed oval and T3 can return the same `Route` contract.

## Senior review — 2026-10-08

Reviewed implementation against T1-01 through T1-06 and the specified route/JSON
contract. Focused tests: 8/8 passed; training runner regressions: 6/6 passed;
program scaffold regressions: 4/4 passed. The fixture length and five handoff
samples agree with the stored geometry. No blocking defect found. T1 is accepted;
T4A and T3 may use the public Route and JSON API.

The broader telemetry UDP socket test has an existing unrelated failure noted
in `docs/telemetry.md`; it was not part of this focused T1 verification.
