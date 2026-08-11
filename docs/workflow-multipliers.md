# Workflow multipliers

This catalog shares reusable advantages discovered in a real agentic workflow.
It is a menu, not a reference architecture: people may use an asset alone,
combine it with other assets, adapt the idea to another tool, or treat it as
inspiration for a different workflow.

The generated [catalog index](../catalog/index.md) is the complete browse
surface; the manifest remains the source of truth for entry identity,
provenance, dependencies, supported targets, and installation. This page is an
editorial guide to recurring friction and useful combinations, not a second
inventory. An omitted entry is not absent from the catalog.

For the practical adoption decision, see the [adoption guide](adoption-guide.md).
For separately owned systems that complement these patterns, see the
[external reference map](external-references.md).

## Adoption modes

- **Standalone** — useful without adopting the rest of this catalog.
- **Companion** — often useful beside another practice, but not a required
  dependency unless the manifest says so.
- **Inspiration** — a transferable reasoning pattern whose implementation can
  be entirely different in another setup.
- **Reference or adapter** — tied to a runtime or external project; useful for
  understanding an integration boundary, not something this repository
  vendors.

No relationship in the tables below is a prescribed order or stack.

## Context and continuity

| Multiplier | Friction it removes | Use it when | Possible companions |
| --- | --- | --- | --- |
| [`repo-aware-context`](../workflows/repo-aware-context/WORKFLOW.md) | The agent loads the wrong documents, mixes policy with live truth, or spends context on irrelevant material. | Work crosses repositories, instruction layers, or unfamiliar code. | [`agentized-task-packet`](../skills/agentized-task-packet/SKILL.md), [`low-always-loaded-instruction-migration`](../skills/low-always-loaded-instruction-migration/SKILL.md) |
| [`low-always-loaded-instruction-migration`](../skills/low-always-loaded-instruction-migration/SKILL.md) | Startup instructions become bloated, duplicated, or contradictory. | A setup has accumulated rules across providers or repositories. | `repo-aware-context`, `agent-config` |
| [`context-budget-governor`](../workflows/context-budget-governor/WORKFLOW.md) | Long sessions degrade as context fills with stale or repetitive material. | A task spans many tool calls, checkpoints, or handoffs. | [`durable-agent-workflows`](../skills/durable-agent-workflows/SKILL.md), `repo-aware-context` |
| [`durable-agent-workflows`](../skills/durable-agent-workflows/SKILL.md) | Interruptions erase the goal, decisions, verification state, or next action. | Work spans sessions, agents, queues, or external state. | `context-budget-governor`, [`governed-work-loop`](../workflows/governed-work-loop/WORKFLOW.md) |
| [`agentized-task-packet`](../skills/agentized-task-packet/SKILL.md) | An ambiguous request becomes an under-scoped delegation. | Another agent or future session needs a bounded, verifiable assignment. | `repo-aware-context`, `durable-agent-workflows` |

## Control and evidence

| Multiplier | Friction it removes | Use it when | Possible companions |
| --- | --- | --- | --- |
| [`governed-work-loop`](../workflows/governed-work-loop/WORKFLOW.md) | The agent jumps from request to edit without routing, verification, or a handoff. | You want a compact mental model for serious work. | `safe-tool-guards`, `durable-agent-workflows` |
| [`safe-tool-guards`](../workflows/safe-tool-guards/WORKFLOW.md) | A shell or tool action has unclear scope, approval, or recovery behavior. | Work can modify files, external state, credentials, or expensive resources. | `governed-work-loop`, [`review-gated-verified-fix`](../skills/review-gated-verified-fix/SKILL.md) |
| [`execution-reassessment`](../skills/execution-reassessment/SKILL.md) | Repeated failures, setup, or lifecycle transitions create the same user churn. | The same remediation has happened twice or a normal lifecycle invalidates trusted state. | `safe-tool-guards`, [`durable-agent-workflows`](../skills/durable-agent-workflows/SKILL.md) |
| [`safe-canonical-branch-folding`](../skills/safe-canonical-branch-folding/SKILL.md) | Branch consolidation can erase dirty, unique, unpublished, or ambiguous work. | Named branches need to be folded into a canonical development line and pruning may follow. | `safe-tool-guards`, [`review-gated-verified-fix`](../skills/review-gated-verified-fix/SKILL.md) |
| [`evaluation-evidence`](../workflows/evaluation-evidence/WORKFLOW.md) | Observations, hypotheses, limitations, and claims get mixed together. | You are comparing behavior, reporting a result, or preserving provenance. | [`repo-behavior-spec-loop`](../skills/repo-behavior-spec-loop/SKILL.md), [`divergent-strategy`](../skills/divergent-strategy/SKILL.md) |
| [`evidence-based-skill-improvement`](workflow-multipliers/evidence-based-skill-improvement.md) | Skills are trusted because they read well instead of because their behavior has been tested. | A repeated skill needs refinement, a static audit identifies a risk, or a candidate is being prepared for sharing. | `skill-harvest-and-promotion`, `repo-behavior-spec-loop`, external evaluation tools |
| [`repo-behavior-spec-loop`](../skills/repo-behavior-spec-loop/SKILL.md) | Expected behavior is implicit and fixes are judged by code presence alone. | A mature repository needs source-derived acceptance and regression evidence. | `evaluation-evidence`, `review-gated-verified-fix` |
| [`review-gated-verified-fix`](../skills/review-gated-verified-fix/SKILL.md) | A remediation can silently cross from proposed fix into accepted change. | A fix needs isolation, verification, and explicit human acceptance. | `safe-tool-guards`, `repo-behavior-spec-loop` |
| [`evidence-backed-change-surface-mapping`](../skills/evidence-backed-change-surface-mapping/SKILL.md) | Impact analysis turns into confident guesses about downstream files or systems. | A change may cross ownership, runtime, or repository boundaries. | `repo-behavior-spec-loop`, `evaluation-evidence` |
| [`consequence-closure`](../skills/consequence-closure/SKILL.md) | An implementation stops at its direct diff while downstream truth, conditional maturity, agent evidence, or reusable advantages remain unresolved. | Live implementation evidence exposes a material cross-surface consequence. | `evidence-backed-change-surface-mapping`, `skill-harvest-and-promotion` |
| [`environment-legibility-audit`](../workflows/environment-legibility-audit/WORKFLOW.md) | A repository has code but does not make its identity, commands, context, or readiness legible to an agent. | Onboarding, maintenance, or fleet work needs bounded remediation evidence. | Pre-CR Suite, Quality Runner, `repo-aware-context` |

## Documentation and sharing

| Multiplier | Friction it removes | Use it when | Possible companions |
| --- | --- | --- | --- |
| [`documentation-as-principles`](workflow-multipliers/documentation-as-principles.md) | Durable facts get duplicated, lose their reason, or drift across instruction surfaces. | A setup needs one authoritative home for policy, configuration, evidence, or handoff state. | [`repo-aware-context`](../workflows/repo-aware-context/WORKFLOW.md), [`low-always-loaded-instruction-migration`](../skills/low-always-loaded-instruction-migration/SKILL.md), [`evaluation-evidence`](../workflows/evaluation-evidence/WORKFLOW.md) |

## Thinking and workflow authorship

| Multiplier | Friction it removes | Use it when | Possible companions |
| --- | --- | --- | --- |
| [`divergent-strategy`](../skills/divergent-strategy/SKILL.md) | The first plausible plan becomes the only plan. | A product, architecture, or workflow decision benefits from materially different candidates and explicit judges. | `evaluation-evidence` |
| [`unknowns-first-exploration`](../skills/unknowns-first-exploration/SKILL.md) | Ambiguous work hardens hidden decisions before the user can react. | The territory is unfamiliar, tacit preferences matter, or a map is needed before implementation. | [`agentized-task-packet`](../skills/agentized-task-packet/SKILL.md), `repo-aware-context` |
| [`recurring-loop-authorship`](../skills/recurring-loop-authorship/SKILL.md) | Repeated personal routines remain trapped in one setup or lose state across runs. | A recurring loop needs a customizable spec, human checkpoints, retries, and durable receipts. | [`durable-agent-workflows`](../skills/durable-agent-workflows/SKILL.md), `safe-tool-guards` |
| [`operating-language`](../skills/operating-language/SKILL.md) | Agents repeatedly spend tokens rediscovering the same vocabulary and decision rules. | A team or project has recurring concepts that should change behavior. | `repo-aware-context`, `durable-agent-workflows` |
| [`research-domain-writing`](../skills/research-domain-writing/SKILL.md) | Research, drafting, fact checking, and style review collapse into one unreliable step. | Domain writing needs a grounded packet and explicit QA stages. | Standalone; optional `rdw` CLI |
| [`terrace`](../skills/terrace/SKILL.md) | A Terrace user has to repeatedly explain how planning, execution, validation, and release work should be routed. | Terrace is already part of the adopter's setup. | Standalone router; requires the external Terrace CLI |
| [`skill-harvest-and-promotion`](../skills/skill-harvest-and-promotion/SKILL.md) | A useful private habit remains trapped in one person's setup or gets copied without its safety boundary. | Repeated behavior is being considered for public reuse. | Any candidate skill; external tools remain references |

## Forward-test status

The four high-signal first-party candidates from the global workflow audit
have now cleared the clean-room promotion gate. They are independent
experimental skills, not a required bundle:

| Candidate | Reusable advantage | Current status |
| --- | --- | --- |
| [`execution-reassessment`](../skills/execution-reassessment/SKILL.md) | Stop repeated execution churn, repair the invalidated boundary, and verify the lifecycle transition before resuming. | Promoted; experimental; 3/3 trigger and 1/1 non-trigger cases passed |
| [`safe-canonical-branch-folding`](../skills/safe-canonical-branch-folding/SKILL.md) | Preserve dirty, unique, remote, and ambiguous work while folding into the canonical development line. | Promoted; experimental; 3/3 trigger and 1/1 non-trigger cases passed |
| [`unknowns-first-exploration`](../skills/unknowns-first-exploration/SKILL.md) | Walk known and unknown quadrants in stages so the user can react before implementation hardens. | Promoted; experimental; 3/3 trigger and 1/1 non-trigger cases passed |
| [`recurring-loop-authorship`](../skills/recurring-loop-authorship/SKILL.md) | Turn a repeated personal loop into a workflow with checkpoints, state, retries, and a stopping condition. | Promoted; experimental; 3/3 trigger and 1/1 non-trigger cases passed |

See the [workflow multiplier audit](mining/2026-07-workflow-multiplier-audit.md)
for provenance, exclusions, and the promotion gate. Other source classes remain
reference-only, adapter-shaped, private, or deferred according to that audit.

## Sharing and installation

| Multiplier | Friction it removes | Use it when | Boundary |
| --- | --- | --- | --- |
| [`agent-config`](../bin/agent-config.mjs) | Bringing a portable asset into a setup risks overwrites, unknown deletes, or silent provider drift. | An adopter wants an explicit audit, dry run, or staged install. | It manages allowlisted public assets; it does not register credentials, login state, or host-managed configuration. |

The [external reference map](external-references.md) lists the related
projects, their reusable advantages, and their boundaries. They are optional
integrations or reference implementations, not a required set. In particular,
Pronto is a downstream consumer of the validated Quality Runner maturity-feed
boundary; neither its implementation nor the private feed is copied here.

## Optional combinations

These are examples of useful relationships, not recipes:

- **Context loss:** `repo-aware-context` + `context-budget-governor` +
  `durable-agent-workflows`.
- **Risky change:** `safe-tool-guards` + `governed-work-loop` +
  `review-gated-verified-fix`.
- **Uncertain impact:** `evidence-backed-change-surface-mapping` +
  `repo-behavior-spec-loop` + `evaluation-evidence`.
- **Impact through completion:** `evidence-backed-change-surface-mapping` +
  `consequence-closure` + `skill-harvest-and-promotion`.
- **Reusable practice:** `operating-language` +
  `skill-harvest-and-promotion`.
- **Skill refinement:** `skill-harvest-and-promotion` +
  `evidence-based-skill-improvement` + `repo-behavior-spec-loop`.
- **Documentation hygiene:** `documentation-as-principles` +
  `repo-aware-context` + `evaluation-evidence`.

An adopter may use only one item, replace any item with a local equivalent, or
ignore these combinations entirely.

## Evidence boundary

The public package proves packaging, safety, provenance, and contract behavior
through its validators and fixtures. It does not claim that every multiplier
improves model quality or developer speed for every user. Those claims require
a local baseline, a defined task set, and measured evidence.

The [public mining report](mining/2026-07-public-skill-mining.md) records what
was promoted, merged, referenced, deferred, or excluded without publishing
private paths, transcripts, runtime state, or host registration details.
