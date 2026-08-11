# Jakye Amos Agentic Setup

A growing magazine of **multipliers** for agent work: prompts, skills,
playbooks, setups, tools, briefs, and references that make useful workflows
more capable, repeatable, or trustworthy.

Each multiplier is an independent entry. Use one, combine a few, adapt an idea,
or follow a reference to its owning project. This is a menu, not a universal
agent stack.

## I use each type for

| Type | Use it when |
| --- | --- |
| **Prompts** | The reusable unit is language for one bounded task or interaction. |
| **Skills** | An agent should recognize a class of work and change its behavior. |
| **Playbooks** | The work needs a repeatable sequence, checkpoints, and verification. |
| **Setups** | A workflow needs configuration or host-specific wiring. |
| **Tools** | Software should perform or verify part of the work. |
| **Briefs** | An idea or specification is ready to hand to an agent. |
| **References** | Another project, example, case study, or pattern is worth inspecting. |

[Browse every multiplier by type, topic, and collection](catalog/index.md), or
use the catalog directly:

```bash
python3 scripts/workbench.py list --featured
python3 scripts/workbench.py list --type skill
python3 scripts/workbench.py list --topic safety
python3 scripts/workbench.py search --query "long context" --json
python3 scripts/workbench.py show context-budget-governor --json
```

## How the repository scales

The README is the cover, not a manually maintained inventory.

- [`catalog/manifest.json`](catalog/manifest.json) is the canonical entry and
  installation inventory.
- [`catalog/taxonomy.json`](catalog/taxonomy.json) defines types and curated
  cross-type collections.
- [`catalog/index.md`](catalog/index.md) is generated from those two sources.
- [`library/<type>/<slug>/`](library/README.md) is the preferred home for new
  authored entries.
- Existing `skills/`, `workflows/`, `adapters/`, and fixture paths stay stable
  for current adopters and appear through the same catalog projection.

Topics and use cases are metadata, not folders. That lets a multiplier appear
under context, safety, writing, or several other concerns without duplicating
its files or choosing one arbitrary home.

Read the [catalog model](docs/catalog-model.md) to add an entry. Regenerate the
human index after a manifest or taxonomy change:

```bash
python3 scripts/workbench.py index --write
python3 scripts/workbench.py index --check
```

The repository validator fails if the generated index is stale or a library
folder disagrees with its manifest type.

## Adopt deliberately

Inspect an entry before installing it:

```bash
python3 scripts/workbench.py install context-budget-governor \
  --target generic --root /tmp/workbench-target --dry-run --json
```

Installation requires an explicit target, defaults to dry-run, copies only
manifest-allowlisted files, and never overwrites an existing file. Adapters are
staged for review. External projects remain references and are not copied.

The [workbench manual](docs/workbench.md) owns setup-engine commands, promotion
admission, private overlays, validation, and safety boundaries. The
[adoption guide](docs/adoption-guide.md) explains standalone, composable, and
inspiration modes. The [workflow multiplier essays](docs/workflow-multipliers.md)
describe recurring friction and useful combinations.

## Public boundary

This public, vendor-neutral repository contains portable contracts and
reviewable setup machinery. Private runtime infrastructure, credentials,
session stores, generated harvests, personal manifests, live mappings, and
unresolved conflicts stay outside the distribution boundary.

The public repository name is `jakyeamos-agentic-setup`; the preserved catalog
identity is `Portable Agentic Workbench`. Existing asset IDs and install paths
remain stable.

See [`AGENTS.md`](AGENTS.md) for repository routing,
[`ATTRIBUTION.md`](ATTRIBUTION.md) for provenance, and
[`SECURITY.md`](SECURITY.md) for reporting guidance.
