# Jakye Amos Agentic Setup catalog

The catalog turns recurring agent failure modes into portable systems for
context management, workflow routing, safety, evaluation, durable handoffs,
and evidence-backed execution. The machine-readable source of truth is
[`manifest.json`](manifest.json); this page is the human index.

The public repository is `jakyeamos-agentic-setup`; the preserved catalog
identity is `Portable Agentic Workbench`. The private companion retains
personal manifests, live mappings, audit evidence, and unresolved conflicts.

Read the [workflow multiplier map](../docs/workflow-multipliers.md) to browse
the catalog by the recurring friction each asset addresses. The map describes
optional relationships, not a required stack or canonical adoption order.
Use the [adoption guide](../docs/adoption-guide.md) when deciding whether to
start with one asset, compose a small set, or use a pattern as inspiration.
The [external reference map](../docs/external-references.md) links related
projects without copying their runtimes or private state.
The [July 2026 audit](../docs/mining/2026-07-workflow-multiplier-audit.md)
records the source families, evidence labels, dispositions, and remaining gaps.

## Manifest-aware setup

The dependency-light Node CLI exposes the same fail-closed setup contract for
audit, drift, doctor, sync, install, bootstrap, and smoke checks:

```bash
pnpm agent-config --help
pnpm audit -- --json
pnpm doctor -- --json
pnpm sync -- --dry-run --json
```

Use `--manifest <path>` for an explicit manifest, `--apply` only after
reviewing a dry run, and `--allow-broad-scan` only when the scan scope is
explicitly approved. Existing destinations, unknown live members, conflicts,
unsupported runtimes, and unsafe paths remain blocked.

## Portable workflow multipliers

| ID | What it provides | Maturity | Install mode |
| --- | --- | --- | --- |
| `context-budget-governor` | 150k-token checkpoint policy and compact handoff template | beta | copy |
| `repo-aware-context` | Repository-first routing and context-layer discipline | beta | copy |
| `environment-legibility-audit` | Evidence-first repository environment audit and remediation plans | experimental | copy |
| `governed-work-loop` | route -> context -> execute -> verify -> handoff | stable | copy |
| `safe-tool-guards` | Dry-run, scope, approval, and verification contract | beta | copy |
| `execution-reassessment` | Stop recurring execution churn and verify lifecycle transitions | experimental | copy |
| `safe-canonical-branch-folding` | Preserve uncertain work while folding named branches into a canonical line | experimental | copy |
| `unknowns-first-exploration` | Four-quadrant map and user reaction before implementation | experimental | copy |
| `recurring-loop-authorship` | Customizable recurring workflow specs with checkpoints and state | experimental | copy |
| `project-compass` | Product-truth reconciliation with honest MVP and complete-product progress | experimental | copy |
| `project-partner` | Candid, codebase-aware conversation about ideas and existing PRDs | experimental | copy |
| `evaluation-evidence` | Sanitized contract fixture and evidence vocabulary | beta | copy |
| `evidence-based-skill-improvement` | Behavioral method for testing and refining skills | experimental | copy |
| `documentation-as-principles` | One-home-per-fact documentation and provenance convention | experimental | copy |
| `research-domain-writing` | Grounded domain-writing skill | stable | copy |
| `terrace` | Terrace workflow router skill | stable | copy |
| `low-always-loaded-instruction-migration` | Inventory and safely migrate durable instruction layers | beta | copy |
| `skill-harvest-and-promotion` | Mine authored behavior into polished public skills | beta | copy |
| `repo-behavior-spec-loop` | Cited behavior ledger, bounded fix loop, and regression report | beta | copy |
| `review-gated-verified-fix` | Isolated remediation with evidence handoff and human acceptance | beta | copy |
| `evidence-backed-change-surface-mapping` | Bounded downstream surface mapping with provenance and freshness | beta | copy |
| `agentized-task-packet` | Bounded task packet for routed, verifiable agent execution | beta | copy |
| `durable-agent-workflows` | Durable goals, artifacts, steering, queueing, and resume state | beta | copy |
| `divergent-strategy` | Explicit portfolio search and evidence-based promotion | beta | copy |
| `operating-language` | Compact vocabulary with triggers, decisions, and completion evidence | beta | copy |

The thirteen additive skills above were mined from first-party authored workflow
patterns and sanitized for portable redistribution. Their logical provenance
and deferred or excluded source classes are recorded in the
[public mining report](../docs/mining/2026-07-public-skill-mining.md).

`evidence-based-skill-improvement` is a portable reference, not an
agent-invoked skill. It documents the method for deciding whether a skill's
behavior improves; static warnings remain investigation signals rather than
outcome evidence.

## Adapters

`adapter-generic`, `adapter-codex`, `adapter-claude`, `adapter-gemini`,
`adapter-cursor`, `adapter-antigravity`, and `adapter-copilot` translate the
portable contracts to host-shaped surfaces. They use `stage` mode and contain
guidance only. Review and register any host hook or project instruction
manually; Cursor and Antigravity remain unverified until those runtimes are
available for a smoke check.

## External references

The catalog records separately owned projects as `external` and `manual`
assets. Use the [external reference map](../docs/external-references.md) for
the advantages, links, and boundaries of TMCP, Pronto, Pre-CR Suite, Quality
Runner, AIOS, and the evaluation/context projects. Their runtimes, generated
outputs, private feeds, and managed files are intentionally not copied.

## Quick inspection

```bash
python3 scripts/workbench.py list --json
python3 scripts/workbench.py search --query "safety" --json
python3 scripts/workbench.py show safe-tool-guards --json
python3 scripts/workbench.py install context-budget-governor \
  --target generic --root /tmp/workbench-target --dry-run --json
```
