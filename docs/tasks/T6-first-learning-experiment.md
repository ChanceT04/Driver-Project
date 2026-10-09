# T6 — Actual learning, checkpoint reload and evaluation

Status: pending T5.

## Deliver

Complete `policy/model.py` and `training/sim_train.py`, integrate `train`
and checkpoint-aware `evaluate`, and update the existing runner where needed.

- Select a small continuous-control method using measured throughput and baselines.
  Consider imitation from the follower, reinforcement learning, or imitation then RL.
  Record the choice; add only justified dependencies to pyproject.toml.
- Implement real learning updates through TrainableAgent. Do not call the diagnostic
  follower a learned policy or count an unchanged policy as training.
- Validate agent settings; reject null/unsupported method. Seed model initialization,
  sampling and environments. Implement fixed-order observation packing and bounded
  action conversion, including simultaneous throttle/brake handling.
- Preserve the runner's split isolation, initial validation and periodic validation.
  Add a validation-only development path: the current runner always performs a final
  test on every invocation, which must not become a tuning feedback loop.
- Declare checkpoint selection (fixed-budget final or validation-selected), save it,
  reload it, and evaluate frozen with exploration and learning updates disabled.
  Test evaluation is reserved for the declared candidate in T10.
- Save resolved config, dependency/schema versions, checkpoints, episode metrics,
  summary and learning curves. Explain whether checkpoints support inference only
  or full training resumption; do not imply optimizer state is saved if it is not.
- Retain a few success/failure replays with the T4A replay format. Keep bulk step
  logging optional. Adapt to an established learner if useful rather than forcing
  its update schedule into an unsuitable custom loop.

## Evidence

Run a bounded real learning experiment and compare initial/final checkpoints,
zero action and follower on identical validation routes. Show that parameters
actually update, and report completion, distance, valid-lap time, seeds, counts
and spread. Reload in a fresh process and reproduce evaluation within stated tolerance.

If learning fails, preserve the honest result and diagnose reward, observation,
physics, optimization or training distribution. Do not substitute a good training
lap for held-out evidence.

## Required acceptance tests

Follow [the shared testing rules](../testing.md). Implement
`tests/test_learning_agent.py`, `tests/test_sim_training.py` and extend
`tests/test_training_framework.py` for the revised final-test behavior.

| ID | Input / exercise | Required result |
| --- | --- | --- |
| T6-01 | Reorder mapping keys for the same observation; provide incompatible schema/shape; drive extreme finite model outputs through action conversion | Packed model input is identical regardless of mapping insertion order. Wrong schema/shape is rejected. Output Action is finite and in bounds, with the documented throttle/brake rule. Nonfinite outputs fail visibly. |
| T6-02 | Fixed nondegenerate training minibatch/rollout with learning enabled; compare parameters before/after | At least one trainable parameter changes, losses/parameters remain finite, and the real optimizer/update code ran. For imitation, fixed supervised loss should decrease in a controlled small fit; for RL, do not require noisy episode reward to rise on every update. |
| T6-03 | Evaluate the same saved model twice with exploration disabled | No learning hooks, optimizer steps or normalization-stat updates. Parameters and preprocessing state are unchanged; actions match within 1e-6 in the declared deterministic CPU mode. |
| T6-04 | Save, exit process, reload; evaluate 20 fixed observations and one seeded episode | Actions match within 1e-6, episode outcome matches and trajectory/progress agrees within the declared numerical tolerance. Missing/corrupt checkpoint or incompatible schema fails clearly. |
| T6-05 | Instrument route requests and transition collection during development training | Training sees only training routes; validation creates no learning transitions; no test routes are requested at all. Test evaluation occurs only through the explicit frozen-candidate path. |
| T6-06 | RL terminal versus time-limit truncation, if the selected method bootstraps | With reward=1, gamma=0.9 and next value=2, terminal target is 1 and truncated target is 2.8. Use an equivalent explicit target for the selected algorithm. Mark this case not applicable, with reason, for pure imitation. |
| T6-07 | CLI training with selected method, bounded budget and fixed seeds; null method, invalid hyperparameter and existing output directory | Valid run performs actual updates and writes consistent resolved config, summaries and reloadable weights. Invalid cases fail before overwriting output. Curves agree with episode logs, including failures. |

Run the two new test files plus runner and scaffold checks. For the real
experiment, freeze 10 validation tracks and two starts each before training
(20 attempts per checkpoint). Compare initial and selected learned policy,
zero action and follower under identical conditions. This is validation,
not the untouched T10 test suite.

Pass gate for software: all deterministic checks, actual parameter updates,
fresh-process reload and bounded end-to-end training pass. Report the change
in validation completion and failure distance. A lack of improvement must be
marked "trainer works; driving improvement not demonstrated", with a specific
follow-up experiment; neither parameter changes nor a falling loss prove driving.

## Handoff

Update the task index, working commands and configuration. T10 should be able to
run and inspect the entire program from these artifacts.
