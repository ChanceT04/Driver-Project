# Existing training framework

The generic runner works with toy test environments. Driving physics and learning
are still unfinished. See [architecture](architecture.md) for the program contract
and [task index](tasks/README.md) for owners and implementation order.

## Implemented

- `training/interfaces.py`: bounded Action, StepResult, Transition, DrivingEnvironment,
  TrainableAgent. Training transitions intentionally omit private metrics.
- `training/experiment.py`: episode stepping, separate whole-route seed sets,
  initial/periodic/final validation, per-episode logs and checkpoint calls.
- `training/config.py`: schema-v1 JSON envelope and experiment-field validation.
  Feature-specific settings still require validation by their ticket owner.
- `cli.py` and `scripts/sim.py`: help, config inspection and routing to explicit
  unfinished feature entry points.

The runner's checks establish bookkeeping and isolation. They do not test driving.

## Integration work still assigned

T4A implements DrivingSimulator with a fixed route provider, initial common
observations, diagnostic follower and replay. T3 supplies generated routes;
T4B connects them and extends dynamics. T5 finalizes observations, reward and metrics.
T6 supplies real learning, packing/normalization, checkpoint load and CLI assembly.
T10 verifies the complete program.

The runner currently saves the final in-memory agent and always evaluates it once
on test routes at the end of each invocation. T6 must add validation-only development
runs and explicit candidate selection/reload before T10 performs final testing.
Its current config.json contains runner settings only; the program must also save
resolved vehicle, observation, reward, generator and model settings.

A stateless first policy matches the current interface. Recurrent state, resume
support, parallel environments and optimized batching require deliberate additions
if evidence justifies them; they are not existing capabilities.
