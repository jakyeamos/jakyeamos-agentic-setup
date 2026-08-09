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

## Promotion admission from `ai-workflow-leverage`

`ai-workflow-leverage` owns private discovery, testing, quantification, and the
`leverage-promotion-candidate/v1` packet. JAS consumes that packet only at an
admission boundary. A separate sanitized projection supplies the public asset
metadata; private source references, evidence, paths, and runtime details are
never copied into the catalog plan.

There are two promotion destinations. A portable candidate uses the v1 public
projection and produces a manifest-review plan. A private-only candidate must
also carry a sanitized `private_package` descriptor with an artifact reference,
relative package files, entrypoints, and redaction status. Its v2 projection
produces a private-overlay review plan; the package content stays in a private
root supplied at install time and never enters this repository.

Use the report-only admission commands from the JAS root:

```bash
pnpm promotion-admission validate \
  --candidate /path/to/leverage-candidate.json \
  --projection /path/to/jas-public-projection.json \
  --json
pnpm promotion-admission plan \
  --candidate /path/to/leverage-candidate.json \
  --projection /path/to/jas-public-projection.json \
  --json
pnpm promotion-admission admit \
  --candidate /path/to/leverage-candidate.json \
  --projection /path/to/jas-public-projection.json \
  --approval /path/to/jas-approval.json \
  --json
```

`validate` and `plan` report whether the candidate is eligible. `admit` still
requires explicit human approval and emits `ready_for_manifest_review`; all
three commands report `mutated: false`. The catalog is not edited implicitly,
so a reviewer can inspect the emitted asset and source-map entry before making
the normal manifest change. A v2 `private-overlay` projection also reports
`mutated: false`, requires the same explicit approval, and emits a sanitized
overlay object for review. It does not edit `catalog/manifest.json` or write
the overlay file for you. The v1 private-overlay projection remains a legacy
blocked form; use v2 for a private-only package.

The explicit apply boundary is used by Pronto after the owner accepts a
complete candidate in its Promotion tab:

```bash
pnpm promotion-admission apply \
  --candidate /path/to/leverage-candidate.json \
  --approval /path/to/jas-approval.json \
  --mode public \
  --root /absolute/path/to/jakyeamos-agentic-setup \
  --apply --json
```

The candidate may carry its sanitized projection inline; otherwise pass it with
`--projection`. `apply` still requires the separate approval artifact and the
explicit `--apply` flag. It validates and preflights before changing the public
catalog, private overlay, or private package install target, reports
`JAS_APPLIED` or `JAS_ALREADY_APPLIED`, and is idempotent. `defer` and `reject`
never reach this command. Pronto records the sanitized result back into AWL so
refreshing the inbox does not lose the admission state.

## Public base and private personal overlay

The public JAS base is the friend-to-friend distribution target: use the
catalog and the normal manifest commands without an overlay. A personal
machine can add a separate JSON file kept outside this repository. v1 overlays
contain only public asset IDs, target mappings, and symbolic destinations. v2
overlays may additionally contain sanitized private asset metadata, relative
package paths, and artifact references; the actual package content is supplied
through `--private-root` at install time. Neither form contains private
evidence, host paths, credentials, or unresolved runtime state. The contract is
[`schemas/jas-private-overlay.schema.json`](schemas/jas-private-overlay.schema.json).

Example private file:

```json
{
  "schema_version": "jas-private-overlay/v1",
  "visibility": "private-overlay",
  "overlay_id": "personal-agentic-setup",
  "base_workbench_id": "portable-agentic-workbench",
  "references": [
    {
      "id": "codex-context-budget",
      "asset_id": "context-budget-governor",
      "enabled": true,
      "targets": ["codex"],
      "destination": "$HOME/.codex/workbench/context-budget-governor"
    }
  ]
}
```

Resolve it report-only against the public base:

```bash
pnpm agent-config overlay \
  --overlay "$HOME/.config/jas/private-overlay.json" --json
```

The resolver checks the public workbench identity, asset eligibility, target
support, and symbolic path safety. It never edits the catalog or the private
file. For a v2 overlay containing private-only packages, the one-step install
path is still explicit and disposable:

```bash
pnpm agent-config overlay-install \
  --overlay "$HOME/.config/jas/private-overlay.json" \
  --private-root "$HOME/.config/jas/private-packages" \
  --root /tmp/jas-target --dry-run --json

pnpm agent-config overlay-install \
  --overlay "$HOME/.config/jas/private-overlay.json" \
  --private-root "$HOME/.config/jas/private-packages" \
  --root /tmp/jas-target --apply --json
```

The target root represents the destination machine during review; `$HOME`
destinations in the overlay are mapped inside that root. The installer refuses
the real home directory for ordinary manual installation; the narrow Pronto
promotion path can explicitly authorize the exact real home target after the
JAS admission checks. It still refuses missing sources, existing targets,
unsafe symlinks, and partial preflight plans, and never overwrites an existing
file. The v2
projection contract is documented in
[`schemas/jas-promotion-projection.schema.json`](schemas/jas-promotion-projection.schema.json).

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
- `consequence-closure` - close material downstream impacts, preserve
  conditional maturity, expose relevant UI-only evidence to agents, and raise
  reusable candidates with exact blockers.
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
