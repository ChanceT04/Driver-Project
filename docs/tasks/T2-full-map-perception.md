# T2 — Full-map route and player-pose feasibility

Status: **planned; assign after T1 review**.

This is the game-perception branch. It can proceed after T1 independently of the
offline program; T4A/T3/T4B/T5/T6 do not wait for it. Implement the existing
`perception/hud_route.py` and `player_marker.py` interfaces. The three originals
in `data/maps/reference/` are additional evidence; see that directory's README.
Save overlays and measurements under a new `runs/<name>/` directory. Add a small
read-only analysis command when implementing this ticket.

## Objective

Use the real Melbourne clip to prove that a full-map HUD frame yields an ordered route and that the player triangle yields position and heading. Do not build a universal vision system yet.

## Work

- Decode sampled frames from `C:/Users/Chance Larson/Videos/Radeon ReLive/F1 25/F1 25_2026.10.08-19.56_1.mp4` without altering the recording. Declare any small video/image dependency added.
- Crop the fixed HUD region and extract an ordered closed route in **HUD pixels** through T1. Treat the graphic as a route guide, not measured road width. Show ambiguities such as occlusion, crossings, sector markers, and background interference. A labeled manual trace is acceptable as a comparison or fallback.
- Detect the player **triangle**, including its heading, at multiple times. The circle is the ghost. Emit timestamp, HUD x/y, heading, confidence or missing status, route progress, and lateral pixel offset. Never pair these frames with the Monza telemetry.
- Save diagnostic overlays with route order, selected marker, and failed detections. Keep generated artifacts local; do not commit the MP4.

## Acceptance evidence

- Human inspection of overlays at the start, middle, and end, including distinctive bends and start/finish. Report route breaks, false branches, marker jumps, missing frames, and whether map orientation stays fixed in the inspected sample.
- Focused synthetic tests may support the parser, but the real clip is the deciding evidence. Fail visibly where extraction is ambiguous rather than fabricating a clean route.

## Out of scope

Metre calibration, live screen capture, UDP synchronization, policy training, and game control.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Implement
`tests/test_hud_perception.py`; keep small labelled synthetic fixtures in tests/
and derived real-frame annotations/overlays in a new runs/ directory.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T2-01 | Synthetic triangle at known centres, headings 0, pi/2, pi and -pi/2, plus a separate circle | Detect triangle rather than circle; centre within 1 pixel and wrapped heading error within 2 degrees for clean sufficiently large fixtures. Declare image axes and use enough marker resolution for this tolerance. |
| T2-02 | Blank frame, circle only, partly occluded/ambiguous triangle, and two indistinguishable candidates | No confidently valid invented pose. Missing/ambiguous result is explicit with null fields; no previous-frame position is silently reused. |
| T2-03 | Known synthetic closed route, sector-like decorations and player marker overlaid | Route stays ordered and closed without following decorations/marker edges as new branches. An unresolved broken/ambiguous route fails visibly. Do not infer physical width. |
| T2-04 | Nonzero crop origin and a resized image/config mismatch | Coordinates use the documented full-frame or crop frame consistently; a landmark projects back to the original pixel location. Unsupported resolution/crop fails rather than shifting pose silently. |
| T2-05 | Existing output directory and unreadable image/video | Actionable error; original assets and prior overlays remain unchanged. |

Run:
`python -m unittest discover -s tests -p "test_hud_perception.py" -v`.

Real-input gate: preselect 12 evenly spaced frames from the available clip, retaining
start/middle/end coverage. Alternate six development and six validation frames;
record timestamps before tuning. Manually annotate triangle centre/heading and
at least 12 route landmarks on a clear reference frame. Keep annotations independent
of extracted results. Inspect all three user screenshots and record track/HUD
facts only where visible.

Initial diagnostic target: at least five of six validation-frame poses accepted
within 3 full-resolution pixels and 10 degrees of the manual labels; every accepted
pose meets those bounds, and other frames are explicitly missing/ambiguous.
Route error at annotated visible landmarks is at most 3 pixels with no false
branch or travel-order reversal. These thresholds assess the current clip only,
not game-control readiness. If the triangle is too small to label to those
tolerances, record the measurement limit and agree a revised target before scoring.

Deliver overlays for all 12 frames, with failures retained and source-coordinate
labels. If no independent visual review is available, mark real-input acceptance
pending even when synthetic tests pass.
