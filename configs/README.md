# Experiment configurations

offline.example.json is the schema-v1 structural example, with provisional
physics/reward values and no selected learning method. Its small route splits
are for development; they are not evidence of generalization.

Check the shared envelope with:
`python scripts/sim.py check-config --config configs/offline.example.json`

This checks section presence and experiment bookkeeping only. Feature owners
must validate their section's supported fields, ranges and interactions.
See [architecture](../docs/architecture.md) for ownership and units.
T6 replaces the null method in a concrete experiment config; T10 adds measured
smoke/training configs. Output paths are passed on the command line, so examples
contain no machine-specific absolute paths.
