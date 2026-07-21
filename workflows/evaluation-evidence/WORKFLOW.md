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

## Capture the result

Use the compact fixture in `fixtures/evaluation/contract-fixture.json` as a
shape reference. External contract projects such as
[agent-eval-contract](https://github.com/jakyeamos/agent-eval-contract) remain
the source of any richer schema or runtime behavior; this workbench does not
vendor them.

Never claim a performance improvement from a clean exit code or a smaller
checkpoint alone. A performance claim needs a measured baseline, comparable
inputs, and a recorded method.
