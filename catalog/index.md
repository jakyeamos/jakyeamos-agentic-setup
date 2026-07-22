# Portable Agentic Workbench catalog

The catalog turns recurring agent failure modes into portable systems for
context management, workflow routing, safety, evaluation, durable handoffs,
and evidence-backed execution. The machine-readable source of truth is
[`manifest.json`](manifest.json); this page is the human index.

## Portable workflows and skills

| ID | What it provides | Maturity | Install mode |
| --- | --- | --- | --- |
| `context-budget-governor` | 150k-token checkpoint policy and compact handoff template | beta | copy |
| `repo-aware-context` | Repository-first routing and context-layer discipline | beta | copy |
| `environment-legibility-audit` | Evidence-first repository environment audit and remediation plans | experimental | copy |
| `governed-work-loop` | route -> context -> execute -> verify -> handoff | stable | copy |
| `safe-tool-guards` | Dry-run, scope, approval, and verification contract | beta | copy |
| `evaluation-evidence` | Sanitized contract fixture and evidence vocabulary | beta | copy |
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

The nine additive skills above were mined from first-party authored workflow
patterns and sanitized for portable redistribution. Their logical provenance
and deferred or excluded source classes are recorded in the
[public mining report](../docs/mining/2026-07-public-skill-mining.md).

## Adapters

`adapter-generic`, `adapter-codex`, `adapter-claude`, `adapter-cursor`, and
`adapter-copilot` translate the portable contracts to host-shaped surfaces.
They use `stage` mode and contain guidance only. Review and register any host
hook or project instruction manually.

## External references

The catalog also records AIOS, TMCP, Quality Runner, agent-eval-contract,
context-compiler-contract, and a Gemini surface reference. These entries are
`external` and `manual`; their runtimes, generated outputs, and managed files
are intentionally not copied.

## Quick inspection

```bash
python3 scripts/workbench.py list --json
python3 scripts/workbench.py search --query "safety" --json
python3 scripts/workbench.py show safe-tool-guards --json
python3 scripts/workbench.py install context-budget-governor \
  --target generic --root /tmp/workbench-target --dry-run --json
```
