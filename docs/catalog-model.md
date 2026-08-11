# Catalog model

The repository is a magazine for practical agent-workflow multipliers. A
**multiplier** is anything that makes agent work more capable, repeatable, or
trustworthy. An **entry** is the machine-readable record that lets people and
agents find, inspect, and adopt one.

Those words have different jobs:

- **Multiplier** is the editorial noun used when talking to people.
- **Entry** is the structural noun used in manifests, validation, and tooling.
- **Asset** remains the compatibility noun for installable catalog payloads.

## Three independent dimensions

Every entry can be understood through three questions:

1. **Type — what is it?** Prompt, skill, playbook, setup, tool, brief, or
   reference.
2. **Topic — what does it concern?** Context, safety, research, verification,
   routing, or any other lowercase slug. Topics are many-to-many.
3. **Use case — why would I open it?** A concrete job such as recovering a
   long-running task, reviewing a risky change, or grounding domain writing.

Type determines the preferred physical home. Topics and use cases stay in
metadata because one entry can address several of them. This avoids duplicate
files and a folder tree that has to choose one arbitrary topic.

## Canonical sources

| Fact | Canonical source |
| --- | --- |
| Entry identity, files, maturity, provenance, dependencies, and installation | [`catalog/manifest.json`](../catalog/manifest.json) |
| Type definitions, kind defaults, and curated collections | [`catalog/taxonomy.json`](../catalog/taxonomy.json) |
| Human browse index | Generated [`catalog/index.md`](../catalog/index.md) |
| Preferred new-entry layout | [`library/README.md`](../library/README.md) |
| Setup and admission behavior | [`docs/workbench.md`](workbench.md) |

The README is a cover, not an inventory. It explains the publication and
points at generated or canonical surfaces.

## Entry projection

The CLI preserves every existing asset field and adds an `entry` object when
listing, searching, or showing the catalog:

```json
{
  "entry": {
    "type": "skill",
    "topics": ["context-management", "handoff"],
    "use_cases": [],
    "why": "A concise reason to open the entry.",
    "use_when": null,
    "avoid_when": null,
    "source_path": "skills/example"
  }
}
```

For existing assets, type is derived from `kind`, topics fall back to
`capabilities`, and `why` falls back to `summary`. New or newly curated assets
can override the editorial projection with an `editorial` object:

```json
{
  "editorial": {
    "type": "brief",
    "topics": ["product-strategy", "research"],
    "use_cases": ["agent-handoff"],
    "why": "Turn an unsettled product idea into a bounded agent assignment.",
    "use_when": "The idea is concrete enough to investigate but not implement.",
    "avoid_when": "The task already has an accepted specification."
  }
}
```

Existing entries may omit editorial fields that add no information and use the
derived fallbacks. New AWL promotions use `jas-promotion-projection/v3` and
must supply all six editorial fields so a newly admitted multiplier is
browsable on arrival. Runtime facts such as dependencies, maturity, and
installation never belong in the editorial override.

## Browse and maintain

```bash
python3 scripts/workbench.py list --type skill
python3 scripts/workbench.py list --topic context-management
python3 scripts/workbench.py list --featured --json
python3 scripts/workbench.py search --query "risky change" --json
python3 scripts/workbench.py index --check
```

`index --write` is the only supported way to refresh `catalog/index.md`. The
repository validator fails when the generated index is stale, which prevents a
new manifest entry from silently disappearing from the human browse surface.
