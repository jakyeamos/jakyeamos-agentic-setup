# Limitations

This packaged skill is agent-first. It includes routing config and stage prompts, but it does not include a web crawler, model runner, or publishing pipeline.

## Boundaries

- The agent must gather facts with host tools.
- The skill does not guarantee domain correctness without current, relevant evidence.
- The optional `rdw` CLI can validate and plan prompt bundles when installed, but the CLI is not required for the skill to work.
- Batch work is prompt-driven unless the host project has its own automation around the emitted task plans.

## Failure Modes

- Skipping research produces fluent but shallow copy.
- Skipping domain QA lets jargon misuse and overclaiming survive.
- Letting the humanizer/blader add facts breaks the pipeline.
- Reusing stale packets without checking dates and source notes creates plausible but outdated writing.
