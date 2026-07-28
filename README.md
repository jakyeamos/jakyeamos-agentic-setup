# Jakye Amos Agentic Setup

## Portable Agentic Workbench

I turn recurring AI-agent failure modes into portable systems for context
management, workflow routing, safety, evaluation, and durable handoffs.

This repository is a curated, vendor-neutral workbench for agents and the
people evaluating how I adapt AI systems to real work. It packages reusable
workflow contracts and a growing set of backward-compatible skills while
keeping private runtime infrastructure, managed vendor configuration,
generated harvests, session stores, and credentials outside the distribution
boundary.

The public canonical repository is `jakyeamos-agentic-setup`. The preserved
`Portable Agentic Workbench` catalog identity and existing asset IDs remain
stable for consumers. A private companion holds personal manifests, concrete
live mappings, audit evidence, and unresolved conflicts.

## Start here

The catalog is the source of truth:

```bash
python3 scripts/workbench.py list --json
python3 scripts/workbench.py search --query "long context" --json
python3 scripts/workbench.py show context-budget-governor --json
python3 scripts/workbench.py install context-budget-governor \
  --target codex --root /tmp/workbench-target --dry-run --json
```

Read [`AGENTS.md`](AGENTS.md) for the agent mining contract,
[`catalog/index.md`](catalog/index.md) for the human index,
[`docs/workflow-multipliers.md`](docs/workflow-multipliers.md) to browse the
advantages by recurring friction, [`docs/mining/2026-07-workflow-multiplier-audit.md`](docs/mining/2026-07-workflow-multiplier-audit.md)
for the evidence-backed audit, [`docs/adoption-guide.md`](docs/adoption-guide.md)
for standalone versus composable adoption, [`docs/external-references.md`](docs/external-references.md)
for related projects, and [`docs/mining.md`](docs/mining.md) for the inspection
workflow.

## Manifest-aware setup

The repository also includes a dependency-light Node setup engine for explicit,
fail-closed configuration work:

```bash
pnpm agent-config --help
pnpm audit -- --json
pnpm drift -- --json
pnpm doctor -- --json
pnpm sync -- --dry-run --json
pnpm agent-config install --dry-run --json
pnpm bootstrap -- --dry-run --json
pnpm smoke -- --json
```

Pass `--manifest <path>` to select a manifest, `--apply` only after reviewing
the plan, and `--allow-broad-scan` only with explicit approval. The engine
does not overwrite existing targets, delete unknown live members, resolve
unresolved conflicts, or handle credentials, login, CAPTCHA, MFA, or GUI-only
setup.

## Curated surfaces

These are independent workflow multipliers. Adopt them standalone, combine
them with local practices, or use them as inspiration; this repository does
not prescribe one universal operating model.

- `context-budget-governor` - checkpoint and compaction policy with a 150,000
  estimated-token hard boundary and a reviewable handoff template.
- `repo-aware-context` - repository-first routing that separates policy, live
  truth, reference, evidence, and handoff context.
- `governed-work-loop` - route -> context -> execute -> verify -> handoff.
- `safe-tool-guards` - dry-run, target, approval, and verification contract for
  shell and tool actions.
- `execution-reassessment` - stop recurring execution churn, repair the
  invalidated boundary, and verify the lifecycle transition before resuming.
- `safe-canonical-branch-folding` - consolidate named branches while preserving
  uncertain work and separating integration, publication, and pruning authority.
- `unknowns-first-exploration` - walk four unknown quadrants and hand over a
  user-reactable map before implementation hardens decisions.
- `recurring-loop-authorship` - turn repeated routines into customizable,
  human-controlled workflow specifications with durable state and checkpoints.
- `project-compass` - reconcile changing product truth with what is planned,
  implemented, and genuinely verified while tracking MVP and complete-product
  progress.
- `project-partner` - provide a candid, codebase-aware coworker for exploring
  product ideas, existing PRDs, and engineering tradeoffs without prematurely
  formalizing them.
- `evaluation-evidence` - sanitized contract fixture and vocabulary for
  observed evidence, hypotheses, and limitations.
- `evidence-based-skill-improvement` - treat skills as behavioral hypotheses;
  test triggers, outputs, controls, and regressions before promotion.
- `documentation-as-principles` - keep one home for each fact, explain why it
  exists, and route readers to the source of truth rather than mirroring it.
- `research-domain-writing` - research -> packet -> draft -> QA -> style skill.
- `terrace` - router skill for Terrace planning, execution, validation, review,
  and release-readiness work.
- `low-always-loaded-instruction-migration` - instruction-layer inventory,
  conflict ledger, and no-overwrite migration workflow.
- `skill-harvest-and-promotion` - first-party source mining and public-safety
  promotion gate.
- `repo-behavior-spec-loop` - cited behavior ledger and bounded fix/retest loop.
- `review-gated-verified-fix` - isolated, evidence-backed remediation handoff.
- `evidence-backed-change-surface-mapping` - bounded downstream surface
  discovery with explicit uncertainty.
- `agentized-task-packet` - targeted context, boundaries, verification, and
  handoff packet for delegated work.
- `durable-agent-workflows` - resumable goals, artifacts, steering, and
  approval-gated automation.
- `divergent-strategy` - portfolio exploration with explicit judges and
  promotion criteria.
- `operating-language` - behavior-changing vocabulary with a Leading Word
  Test and completion evidence.

Codex, Claude, Gemini, Cursor, Antigravity, Copilot, and generic adapters are
available as staged manual-review mappings. The public package does not claim
that any adapter can register live host configuration automatically; Cursor
and Antigravity remain explicitly unverified until available for smoke checks.

## Install safely

Installation requires an explicit target root, defaults to dry-run, copies only
manifest allowlisted files, never overwrites an existing file, and reports
missing dependencies without installing them. Adapter and hook-shaped assets
are staged for review; nothing is silently registered in a real home
configuration.

Apply into a disposable directory after reviewing the plan:

```bash
python3 scripts/workbench.py install context-budget-governor \
  --target generic --root /tmp/workbench-target --apply --json
```

The original copyable skill paths remain available for hosts that do not use
the catalog installer:

```bash
AGENT_SKILL_ROOT=/path/to/agent-skills
mkdir -p "$AGENT_SKILL_ROOT"
cp -R skills/research-domain-writing "$AGENT_SKILL_ROOT/research-domain-writing"
cp -R skills/terrace "$AGENT_SKILL_ROOT/terrace"
```

`research-domain-writing` may use the optional external `rdw` CLI, and
`terrace` requires the external `terrace` CLI. The package never installs
those dependencies for you.

The additional skills are also plain `skills/<id>/SKILL.md` packages and are
listed in `catalog/manifest.json`; use the catalog installer when you want the
supporting workflow and fixture files staged together.

## Validation and clean-room check

The catalog runtime uses only Python's standard library:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm check
python3 scripts/pre_cr_coverage.py
```

The individual validator entrypoints remain available for diagnosis:

```bash
python3 scripts/validate_skills.py
python3 scripts/validate_catalog.py
python3 scripts/validate_prevention_pack.py
python3 scripts/public_safety_check.py
python3 scripts/workbench.py validate
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/pre_cr_coverage.py
```

The manifest engine uses Node's standard library and its tests run with
`pnpm test` (which invokes `node --test`).

The tests install into a disposable temporary directory and do not require
Codex, Claude, Cursor, Copilot, Gemini, AIOS, TMCP, Quality Runner, or any
external CLI. The clean-tree `pre-cr run` command may report that no coverage
result was produced when there is no changed diff; run it against a non-empty
feature diff as part of release review.

## Evidence boundary

Case studies explain problem -> mechanism -> evidence -> limitation for
compaction, routing, safety guards, governed execution, and portable skill
distribution. They distinguish observed configuration and command behavior
from hypotheses. No case study claims a model-quality or performance gain
without a measured baseline.

See [`ATTRIBUTION.md`](ATTRIBUTION.md) and [`SECURITY.md`](SECURITY.md) for
provenance, redistribution, and reporting guidance.

Related projects such as TMCP, Pronto, Pre-CR Suite, Quality Runner, AIOS, and
the evaluation/context contracts are linked in the
[external reference map](docs/external-references.md). They remain optional,
separately owned integrations; this repository does not copy their runtimes or
private state.
