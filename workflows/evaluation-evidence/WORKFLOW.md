# Evaluation and evidence loop

Use this workflow when an agent claims that a workflow is safer, more portable,
more reliable, or otherwise better.

## Record the contract

Define the task, input fixture, expected output shape, acceptance conditions,
and the environment assumptions. Keep the fixture sanitized and deterministic.

## Separate evidence types

- **Observed evidence:** a command result, test result, diff, or review finding
  that can be reproduced from the repository.
- **Hypothesis:** a plausible explanation or expected benefit that has not been
  measured by the current fixture.
- **Limitation:** a missing host, dependency, credential, sample, or comparison
  that prevents a stronger conclusion.

Bind every claim to evidence rather than file presence or plan completion. A
claim that cannot be supported becomes a hypothesis or limitation; record its
source, method, baseline, comparable inputs, confidence, freshness, and
unresolved boundary. Merge related claims into one evidence row instead of
creating a new artifact for every synonym.

## Capture the result

Use the compact fixture in `fixtures/evaluation/contract-fixture.json` as a
shape reference. External contract projects such as
[agent-eval-contract](https://github.com/jakyeamos/agent-eval-contract) remain
the source of any richer schema or runtime behavior; this workbench does not
vendor them.

Never claim a performance improvement from a clean exit code or a smaller
checkpoint alone. A performance claim needs a measured baseline, comparable
inputs, and a recorded method.

## Comparable rerun checklist

For a before/after claim, rerun the same workload on the same hardware and
software/runtime, with the same dataset, warmup policy, command/configuration,
sample count, and measurement method. Retain raw measurements (or a bounded
summary such as count, median, and spread) plus the output-equality check.
Different hardware, data, warmup, commands, or missing raw measurements make
the comparison a hypothesis or limitation, not a measured improvement.
