# T3 — Varied generated tracks

Status: pending T1. Dependencies: T1; can proceed independently of T4A.

## Deliver

Implement `track/procedural.py`: generate_route and preview_tracks, exposed
through the existing `preview-tracks` command.

- Seeded closed routes in map metres with explicitly synthetic width.
- Vary lengths, left/right sequences, straight lengths and corner radii within
  validated config bounds. Reject unsupported track settings.
- Reject self-intersections, spikes, unusable radii and corridor overlaps that would
  make progress ambiguous. Bound retries; report failures rather than hang.
- Use whole-layout train/validation/test seeds from ProgramConfig. Check duplicate
  or equivalent layouts across splits; seeds alone do not guarantee diversity.
- Save a labelled visual contact sheet and generation statistics in a new run folder.

## Evidence

Repeatability, closure, spacing, curvature/width feasibility and bounded-failure tests.
Inspect a representative batch including easy and tight layouts. Report rejected
seeds and distribution of route length/curvature. Generated output uses T1 geometry.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Implement
`tests/test_procedural_tracks.py`.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T3-01 | Generate seeds 0, 7 and 99 twice with the same settings, including one fresh process | Same coordinates, width and generation metadata, excluding wall-clock timestamps. Record generator version. |
| T3-02 | QA seeds 0 through 99 using the declared default generator settings | All 100 requested routes are accounted for. Every returned route passes independent closure, finite-value, minimum-spacing, configured length/width/radius and nonintersection checks. Acceptance requires 100 valid routes within the retry budget; log failures rather than silently replacing seeds. |
| T3-03 | Deliberately crossing polyline, overlapping nonadjacent road corridors, tiny spike; impossible config or forced invalid candidates | Geometry checker rejects each fixture. Invalid settings fail before generation; repeated bad candidates stop at max_generation_attempts. Test retry counts instead of relying on a long timeout. |
| T3-04 | Exact copy of a route with cyclically shifted points, then rigid translation/rotation, assigned across artificial splits | Duplicate/equivalent-layout check detects those copies using a stated geometric tolerance. Genuine distinct fixtures remain distinct. Do not use the generator itself as the only validator. |
| T3-05 | QA batch diversity | No duplicate-equivalent layouts in the 100-route batch. Show min/median/max length and bend-radius measures, plus layouts containing both turn directions. A batch of scaled identical ovals does not satisfy varied-route acceptance. |
| T3-06 | Preview command into a new directory; then the same existing directory | First command writes labelled seed/split previews and counts that match the requested routes. Second fails without changing existing files. |

Run:
`python -m unittest discover -s tests -p "test_procedural_tracks.py" -v`
and `preview-tracks` through the documented CLI.

Use QA seeds 0..99 for these geometry checks; reserve the later T10 driving-test
suite. The QA batch is not a generalization result. Inspect a 12-layout contact
sheet chosen by a fixed rule (including shortest, longest and tightest cases),
and record any odd geometry. Pass gate: all structural checks and diversity
requirements pass; preview inspection finds no unresolved geometry defect.

## Handoff

Report generator version, seed behavior, supported config and preview path.
Do not implement physics, reward or learning.
