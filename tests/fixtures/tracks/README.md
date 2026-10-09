# Small synthetic route fixtures

`oval.json` is a deterministic eight-segment closed loop in `map_metres`.
Coordinates and the synthetic 8 m road width are metres; points are ordered in
the intended travel direction. Its polyline length is
`60 + 4 * sqrt(200)` (about 116.5685 m). The route is a software fixture, not a
trace of a real F1 circuit.

## Public route API and schema-v1 JSON

`f1_agent.track.geometry.Route` stores an ordered tuple of `Point2D`, an
explicit `frame`, a non-empty `source`, and optional positive `width` with
`width_source`. Supported frames are `map_metres` (x right, y up) and
`hud_pixels` (x right, y down). There is no implicit pixel-to-metre conversion.
`sample(s)` and `tangent(s)` wrap signed or out-of-range arc distances. A
projection's lateral offset is positive left of travel in either frame.

Schema v1 is a JSON object with exactly these fields: `schema_version` (integer
1), `frame`, `points` (ordered `[x, y]` pairs), `closed` (`true`), `source`,
`width` (positive number or `null`), and `width_source` (`synthetic`,
`measured`, `estimated`, or `unavailable`). Missing width requires
`unavailable`; a supplied width requires one of the other provenance values.
A repeated final point equal to the first is normalized away. Route geometry
stores the loop implicitly closed; JSON still declares that explicitly.

Projection minimizes Euclidean distance to a segment. Exact distance ties use
the candidate whose wrapped progress is nearest `near_distance`, when supplied;
remaining ties use the lowest segment index. Without a hint, the lowest segment
index wins. At an exact vertex, this makes the incoming segment win when it has
the lower index; tangent sampling itself uses the outgoing segment.

Large generated training distributions and previews belong in ignored `runs/`.
