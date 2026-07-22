# Portable Agentic Workbench catalog

The catalog turns recurring agent failure modes into portable systems for
context management, workflow routing, safety, evaluation, and durable
handoffs. The machine-readable source of truth is
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
