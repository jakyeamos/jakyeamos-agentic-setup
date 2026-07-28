# Workflow Multiplier Audit — July 2026

## Purpose

This audit asks what advantages have accumulated in the author's agentic
workflow and which of those advantages can be shared independently.

It does not define a universal setup, dependency graph, or canonical order.
An audited behavior may be adopted as a standalone skill, combined with a
different local tool, used as a prompt for a new design, or left as private
operating knowledge.

The public catalog's unit of value is the **multiplier**: a repeatable change in
how an agent works that removes recurring friction or makes a failure mode more
legible.

## Audit method

The source set covered:

- public catalog assets, manifest entries, case studies, validators, and
  promoted skills;
- global and provider-specific instruction surfaces, inspected for routing,
  duplication, precedence, always-loaded content, and conflict behavior;
- TMCP's packet, routing, receipt, harvest, and safety contracts;
- Quality Runner's evidence-only audit and redacted maturity-feed boundary;
- Pre-CR Suite's shared project contract, headless gate, and setup workflow;
- AIOS's durable work, shadow-versus-governed routing, context compiler, and
  receipt conventions;
- Agent Router's classification, dispatch, evidence, and learning loop;
- agent-eval-contract and agent-eval-runtime's public-safe record and
  report-only boundaries;
- the private configuration companion's low-always-loaded and conflict-ledger
  model; and
- the research and Terrace workflow surfaces that are already represented in
  the catalog.

Generated artifacts, worktrees, caches, credentials, raw prompts, transcripts,
private paths, browser state, and vendor-managed registration files were not
used as public evidence.

## Evidence labels

- **Observed** — directly supported by a source document, contract, command,
  fixture, or validation result.
- **Promoted** — already reduced to a public catalog asset with a stated
  boundary and validation surface.
- **Candidate** — a recurring behavior is directly observed in a source, but
  it has not yet been sanitized, packaged, and forward-tested as a public
  asset.
- **Reference** — useful external implementation or integration boundary; not
  copied into this repository.
- **Unmeasured** — plausible leverage that still needs a local baseline and
  defined task set before a performance claim is justified.
- **Blocked or unknown** — the source or runtime was unavailable, conflicted,
  or intentionally withheld; it is not treated as evidence of success.

## Source-level findings

### Instruction surfaces

The public design principle is correct: startup surfaces should contain
invariants and routing pointers while detailed procedure lives in on-demand
packets. The live setup does not yet uniformly satisfy that ideal:

- one provider edge is genuinely thin and routes into shared policy;
- other provider edges still contain substantial duplicated defaults and
  workflow policy;
- the provider projections are not all parity-verified;
- one provider's global instruction surface remains unavailable for smoke
  validation; and
- the private companion correctly keeps unresolved conflicts at an audit
  stopping state rather than silently resolving them.

**Disposition:** promote the principle through
[`low-always-loaded-instruction-migration`](../../skills/low-always-loaded-instruction-migration/SKILL.md)
and [`repo-aware-context`](../../workflows/repo-aware-context/WORKFLOW.md);
keep provider projection details private and treat parity as a local setup
check, not a public compatibility claim.

### TMCP

TMCP is more than a skill collection. Its reusable multiplier is compiling a
natural-language objective into a task-specific packet, routing through
source-backed behavior, recording receipts, and recompiling when evidence
changes. Its standalone mode remains useful without AIOS.

Observed boundaries include:

- packet composition and runtime-next are distinct from execution;
- portable harvest excludes secrets, credentials, browser profiles, caches,
  dependency trees, build outputs, and version-control data;
- artifact persistence and receipts have separate safety requirements; and
- experimental recommendation, promotion, and expert-rubric surfaces must not
  be presented as stable runtime guarantees.

**Disposition:** reference TMCP as an optional compiler/runtime and retain the
portable parts in [`skill-harvest-and-promotion`](../../skills/skill-harvest-and-promotion/SKILL.md),
[`agentized-task-packet`](../../skills/agentized-task-packet/SKILL.md), and
[`evaluation-evidence`](../../workflows/evaluation-evidence/WORKFLOW.md).

### Quality Runner and Pronto

Quality Runner contributes a distinct multiplier: audit and plan from evidence
without pretending that a dirty, detached, stale, or unverifiable checkout was
fully validated. Its maturity feed is deliberately redacted and only published
after deterministic replay, provenance, coverage, and privacy checks.

Pronto is observed as a downstream consumer of that feed boundary, not as an
independently audited local source in this pass. No Pronto implementation is
copied or treated as a dependency.

**Disposition:** reference Quality Runner and the feed contract; expose the
Pronto relationship in the public external-reference map and catalog manifest
without claiming Pronto runtime availability or copying its consumer surface.

### Pre-CR Suite

Pre-CR contributes a portable contract pattern: one project-owned configuration
feeds editor clients, headless JSON gates, coverage refresh, and setup repair.
The important multiplier is parity across surfaces, not the editor integration
itself.

**Disposition:** reference Pre-CR as an optional project-local quality surface.
Do not require it for public skills. `environment-legibility-audit` may point
to it as a possible verifier when an adopter already uses it.

### AIOS and the context compiler

AIOS contributes several separable multipliers rather than one required stack:

- ordinary work can use a shadow route as comparison evidence while the
  current workspace remains the baseline;
- governed routing is explicit and failures retain distinct meanings;
- substantial work moves from transcript dependence to reviewable artifacts;
- durable goals declare a verifier and stopping condition; and
- context selection uses signal, specificity, authority, recency, and token
  cost, with receipts explaining loaded, skipped, missing, conflicting, and
  written context.

**Disposition:** keep AIOS and the context compiler as references. Promote the
portable behavior through `durable-agent-workflows`,
`context-budget-governor`, `evaluation-evidence`, and
`repo-aware-context`. Do not publish AIOS storage, hooks, session state, or
shadow-run implementation details.

### Agent Router

Agent Router contributes a useful distinction that should remain visible in the
public model: classification, planning, provider selection, dispatch,
receipts, evidence validation, reviewer synthesis, and learning are separate
states. In particular, discovery/configuration is not execution evidence, and
`not_run`, `awaiting_consent`, `blocked`, `failed`, and `passed` are not
interchangeable.

**Disposition:** reference Agent Router as an optional implementation of
evidence-backed routing. Strengthen public skills where they currently imply
that selecting a tool or composing a packet proves that the work ran.

### Agent evaluation

The contract/runtime split is itself a multiplier. A provider-neutral record
contract can be reused by different runners, while the runtime owns execution,
paired comparisons, benchmarks, and corpus evidence. Report-only defaults,
redacted fixtures, stable IDs, provenance, and `unknown`/`blocked` states keep
evaluation from becoming an unsupported quality claim.

**Disposition:** reference both the contract and runtime. Keep
`evaluation-evidence` as the portable vocabulary and do not vendor-copy
provider clients, raw eval data, or private artifacts.

### Private configuration companion

The private companion is the strongest evidence for the low-always-loaded and
conflict-ledger multipliers. It also demonstrates an important boundary:
manifest authority must not be inferred from the fact that a file happens to
exist in a live provider directory.

**Disposition:** use it as a source for sanitized behavior only. Keep concrete
manifests, live mappings, conflict evidence, private agents, commands, and
provider registration outside this repository.

### Active global skill surface

The global skill surface is a second source of workflow multipliers, but it is
not a public package to mirror wholesale. A bounded harvest matched 117 skill
packages; the configured harvest limit inspected 40 source packages and
reported 24 advisory warnings. No automatic rewrite or promotion was treated
as evidence. The warnings clustered around broad triggers, required reads
buried below the opening contract, and missing observable output contracts.
Those are investigation targets, not proof of poor behavior.

The high-signal first-party candidates and promotion result are:

- **Execution reassessment — promoted:** after repeated failure, repeated
  manual setup, lifecycle invalidation, or an unstable fallback, stop repeating
  the same path; classify the systemic cause; make the smallest execution
  change; and report symptom, cause, change, impact, and verification. The
  revised public contract passed three of three trigger runs and one
  non-trigger run under a separate judge.
- **Safe canonical branch folding — promoted:** fold work into the canonical
  development line only after checking dirty state, unique work, remote truth,
  and ambiguity; preserve uncertain work and avoid force-push or deletion. The
  final public contract passed three of three trigger runs and one non-trigger
  run after adding a structured per-source deletion-authority recheck.
- **Unknowns-first exploration — promoted:** walk known-knowns,
  known-unknowns, unknown-knowns, and unknown-unknowns one stage at a time,
  producing a map that lets the user react before implementation. The final
  public contract passed three of three trigger runs and one non-trigger run
  after making stage order and clean-room scope fallback fail closed.
- **Recurring-loop authorship — promoted:** turn a repeated personal loop into
  a workflow with a trigger, inputs, output/state, tools, human checkpoints,
  failure and retry behavior, and a stopping condition. The final public
  contract passed three of three trigger runs and one non-trigger run after
  requiring one spec dimension per question.
- **Blind skill evaluation:** use fresh runners and a separate judge, positive
  and negative cases, a named control, repeated pass rates, and diagnosis of
  skill defect versus bad case. The public
  [`evidence-based-skill-improvement`](../../docs/workflow-multipliers/evidence-based-skill-improvement.md)
  reference now includes a portable experiment record, separated routing /
  behavior / boundary judgments, and an explicit promotion rule. It remains a
  reference rather than an agent-invoked skill until its own routing and output
  behavior has a broader clean-room corpus.
- **Docs as principles:** keep one home for each fact, document why and the
  non-obvious discovery, and point to the source of truth instead of mirroring
  code or current rosters. The portable
  [`documentation-as-principles`](../../docs/workflow-multipliers/documentation-as-principles.md)
  reference now provides a fact record, authoring loop, handoff prompt, and
  anti-patterns. It remains a convention rather than another mandatory layer.

Other inspected skills are intentionally not first-party public candidates:
engineering-specific refactoring guidance is better treated as a reference;
session retention and setup wizards touch private data or secrets; OpenCLI,
design, and provider-specific skills remain adapters or external references;
and third-party Firecrawl/GSD-style packages are not evidence of the author's
workflow advantage without explicit ownership and provenance.

**Disposition:** `execution-reassessment`, `safe-canonical-branch-folding`,
`unknowns-first-exploration`, and `recurring-loop-authorship` are now public
experimental skills after the clean-room gate used by
[`skill-harvest-and-promotion`](../../skills/skill-harvest-and-promotion/SKILL.md).
The evidence and documentation references are now strengthened, and the
catalog directly indexes external projects without copying them. Keep the
remaining sources reference-only or private. This preserves the catalog's
menu model instead of turning the global skill inventory into a prescribed
bundle.

## Multiplier disposition ledger

| Behavior family | Public representation | Disposition | Evidence state |
| --- | --- | --- | --- |
| Progressive disclosure and low always-loaded policy | `low-always-loaded-instruction-migration`, `repo-aware-context` | Retain and strengthen usage guidance | Observed and promoted |
| Context budget and resumable continuity | `context-budget-governor`, `durable-agent-workflows` | Retain; clarify standalone use | Observed and promoted |
| Bounded delegation | `agentized-task-packet` | Retain; tighten trigger/output examples | Observed and promoted |
| Route/context/execute/verify/handoff discipline | `governed-work-loop` | Retain as a mental model, not a required stack | Observed and promoted |
| Safe side effects and approval boundaries | `safe-tool-guards` | Retain; keep host-specific policy out | Observed and promoted |
| Behavior-first verification | `repo-behavior-spec-loop` | Retain; require source and runtime evidence | Observed and promoted |
| Human acceptance after verified remediation | `review-gated-verified-fix` | Retain; preserve no-auto-merge boundary | Observed and promoted |
| Bounded impact inference | `evidence-backed-change-surface-mapping` | Retain; strengthen unknown/freshness output | Observed and promoted |
| Distinguishing observation from hypothesis | `evaluation-evidence` | Retain as shared vocabulary | Observed and promoted |
| Environment legibility | `environment-legibility-audit` | Retain; reference Pre-CR and Quality Runner optionally | Observed and promoted |
| Competing strategies and explicit judges | `divergent-strategy` | Retain; make the non-trigger clearer | Observed and promoted |
| Shared operating vocabulary | `operating-language` | Retain; emphasize behavior change over terminology | Observed and promoted |
| Grounded domain-writing pipeline | `research-domain-writing` | Retain; external CLI remains optional | Observed and promoted |
| Tool-specific workflow routing | `terrace` | Retain as optional adapter-shaped skill | Observed and promoted |
| Turning personal practice into public skill | `skill-harvest-and-promotion` | Retain as the authoring method | Observed and promoted |
| Task-specific packet compilation and receipts | TMCP reference | Keep external; do not require | Observed and referenced |
| Evidence-only repository/fleet assessment | Quality Runner reference | Keep external; direct catalog link and feed boundary | Observed and referenced |
| Project-local quality parity | Pre-CR Suite reference | Keep external; optional verifier and direct catalog link | Observed and referenced |
| Durable orchestration and context selection | AIOS/context compiler references | Keep external; promote portable contracts only | Observed and referenced |
| Provider/model routing and learning | Agent Router reference | Keep external; preserve state distinctions | Observed and referenced |
| Typed evaluation execution | Agent Eval Contract/Runtime references | Keep external; use contract vocabulary | Observed and referenced |
| Behavioral skill improvement loop | `evidence-based-skill-improvement` | Retain as a strengthened portable reference; require broader corpus before agent invocation | Observed and promoted |
| Reassess after repeated execution failure | `execution-reassessment` | Promote as an experimental public skill; broaden cases before maturity increase | Observed and promoted |
| Safe folding into the canonical development line | `safe-canonical-branch-folding` | Promote as an experimental public skill; increase maturity only with broader branch-policy cases | Observed and promoted |
| Unknowns-first exploration map | `unknowns-first-exploration` | Promote as an experimental public skill; broaden artifact and user-reaction cases before maturity increase | Observed and promoted |
| Recurring loop to workflow specification | `recurring-loop-authorship` | Promote as an experimental public skill; broaden durable-state and adapter cases before maturity increase | Observed and promoted |
| Docs as principles and one-home-per-fact | `documentation-as-principles` | Share as a reference convention; do not require a new layer | Observed and strengthened |
| Engineering refactor ownership | Local engineering reference | Defer as a general agent multiplier; retain as source guidance | Observed; reference |
| Session retention and manifest-bound deletion | Private data-governance source | Exclude implementation; retain only sanitized principles if needed | Intentionally withheld |
| Secret-bearing setup wizard and provider adapters | Host/tool-specific sources | Exclude from the public core; reference only when an adapter is in scope | Intentionally withheld |
| Private provider registration and session infrastructure | Private runtime sources | Exclude from public package | Intentionally withheld |
| Comparative performance or model-quality lift | No shared baseline yet | Defer claim until measured | Unmeasured |
| Standalone Pronto implementation | No independently audited source in scope | Reference through the external map and Quality Runner feed boundary; do not copy | Observed and referenced |

## Cross-cutting conventions worth sharing

These are not tied to one tool and are likely the highest-leverage part of the
workflow:

1. **Read before modifying.** Inspect the current source, ownership, and
   routing context before proposing a fix.
2. **Progressive disclosure.** Keep only hard stops and routing pointers in
   always-loaded surfaces; load detailed packets on demand.
3. **Source versus evidence.** A configured route, generated packet, or planned
   check is not proof that execution occurred.
4. **Unknown is a real state.** Missing, stale, blocked, unverified, and
   awaiting-consent results must remain distinct from pass.
5. **Bounded side effects.** Resolve target, scope, approval, dry-run, and
   verification before mutation.
6. **Artifacts beat transcripts.** Durable goals, receipts, ledgers, fixtures,
   and handoffs should carry the work across sessions.
7. **Human review remains a state transition.** Verified is not accepted,
   published, merged, or submitted.
8. **Mine behavior, not scaffolding.** Extract the reusable decision or safety
   boundary, not private paths, vendor syntax, or a finished personal setup.

## Gaps requiring future work

### High priority

- Tighten broad trigger descriptions and make output contracts explicit for
  the skills identified by the TMCP static audit.
- Add clean-room trigger/non-trigger examples for the public skills whose
  current tests only validate file presence or broad markers.
- Broaden the forward corpus for the three newly promoted experimental skills
  across branch policies, concrete exploration artifacts, and durable workflow
  adapters before raising their maturity.

### Medium priority

- Keep the adoption guide's problem index, invocation types, and optional
  compositions aligned as new assets are added; these are documentation
  surfaces, not machine dependencies.

### Not a goal

- A universal default workflow.
- A provider-parity promise across every host.
- Copying AIOS, TMCP, Quality Runner, Pronto, Pre-CR, or private runtime state.
- A performance or model-quality claim without a baseline and repeated task
  evidence.

## Audit conclusion

The current public set is directionally correct: the most valuable assets are
the portable reasoning and control boundaries, not the author's exact tool
stack. The repository should continue as a catalog of independent workflow
advantages with optional relationships and external references.

The next quality step is not composing a universal profile. It is making every
multiplier independently legible, triggerable, verifiable, and honest about
its evidence. The four high-signal first-party candidates from this pass now
have independent experimental contracts in the public catalog; the adoption
guide, external reference map, and strengthened reference patterns make the
remaining boundaries discoverable without turning them into a required stack.

Audit status: `AUDIT_COMPLETE`. The follow-up promotion cycle promoted
`execution-reassessment`, `safe-canonical-branch-folding`,
`unknowns-first-exploration`, and `recurring-loop-authorship`; no provider
projection or runtime migration was applied.
