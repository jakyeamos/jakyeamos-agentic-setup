# Adoption guide

This repository is a menu of workflow multipliers, not a workflow profile to
install wholesale. Start with one recurring friction, try the smallest useful
asset, and keep or replace it according to the evidence from your own setup.

## Start with the friction

| If your recurring problem is… | Start with… | Add another surface only when… |
| --- | --- | --- |
| The agent loads the wrong context or forgets repository boundaries | [`repo-aware-context`](../workflows/repo-aware-context/WORKFLOW.md) | The task also spans long sessions or needs resumable state |
| Long sessions lose decisions or verification state | [`context-budget-governor`](../workflows/context-budget-governor/WORKFLOW.md) | A durable artifact or cross-session resume is needed |
| Tool actions have unclear scope or approval | [`safe-tool-guards`](../workflows/safe-tool-guards/WORKFLOW.md) | The change also needs a human acceptance boundary |
| The same failed execution path keeps recurring | [`execution-reassessment`](../skills/execution-reassessment/SKILL.md) | The correction needs durable workflow state or a side-effect guard |
| Branch consolidation may erase uncertain work | [`safe-canonical-branch-folding`](../skills/safe-canonical-branch-folding/SKILL.md) | The local branch policy requires a separate review or release step |
| A vague problem is hardening decisions too early | [`unknowns-first-exploration`](../skills/unknowns-first-exploration/SKILL.md) | The resulting map needs delegation or a durable decision record |
| A repeated personal routine is trapped in one setup | [`recurring-loop-authorship`](../skills/recurring-loop-authorship/SKILL.md) | The routine needs durable receipts, retries, or explicit side-effect gates |
| A skill sounds good but its behavior is unproven | [`evidence-based-skill-improvement`](workflow-multipliers/evidence-based-skill-improvement.md) | The candidate needs public-safety promotion or repository-derived regression cases |
| Repository quality claims are hard to verify | [`evaluation-evidence`](../workflows/evaluation-evidence/WORKFLOW.md) | A local quality runner or project contract already exists |
| A useful practice needs to become shareable | [`skill-harvest-and-promotion`](../skills/skill-harvest-and-promotion/SKILL.md) | The behavior has passed clean-room and non-trigger checks |

This is a starting-point map, not a dependency graph. The manifest's
`dependencies` field is the authority for actual install dependencies.

## Choose an adoption mode

### Standalone

Use one asset when it addresses the problem by itself. Copy or stage the files
listed by that manifest record, adapt the names and boundaries to your host,
and ignore the suggested companions unless your own workflow exposes the next
friction.

Standalone adoption is the default. An adopter does not need to adopt
`governed-work-loop`, TMCP, AIOS, or any other surrounding system to use one
portable skill or workflow.

### Composable

Combine assets when each one owns a different decision or artifact. A useful
composition normally has a clear first surface, one or two supporting
surfaces, and a verifier. Keep the contracts separate: do not copy the same
policy into multiple instructions just to make a bundle feel complete.

Examples:

| Goal | First surface | Optional companion | What the companion adds |
| --- | --- | --- | --- |
| Recover from context loss | `repo-aware-context` | `context-budget-governor` | A checkpoint before the context boundary is reached |
| Make a risky change reviewable | `safe-tool-guards` | `review-gated-verified-fix` | Verification and explicit human acceptance |
| Turn uncertainty into an actionable plan | `unknowns-first-exploration` | `agentized-task-packet` | A bounded handoff after the user reacts to the map |
| Refine a recurring skill | `evidence-based-skill-improvement` | `repo-behavior-spec-loop` | Repository-derived cases and regression evidence |

These examples are optional combinations, not recipes. Substitute a local
equivalent whenever it serves the same boundary better.

### Inspiration

Some entries are best read as ideas rather than copied files. The
[`documentation-as-principles`](workflow-multipliers/documentation-as-principles.md)
reference, for example, describes a way to keep one home for each fact,
explain why it exists, and link to the source of truth. A team can implement
that convention in its own docs, issue tracker, or knowledge system without
installing anything here.

### External reference or adapter

External references and adapters are not part of the portable core:

- an **external reference** points to a separately owned project or contract;
  use that project for its runtime and current documentation;
- an **adapter** maps a portable contract to a host surface and requires local
  review before registration;
- neither category authorizes copying private state, generated artifacts,
  credentials, or managed host configuration.

See the [external reference map](external-references.md) for TMCP, Pronto,
Pre-CR Suite, Quality Runner, and the other related projects.

## Invocation types

Use the type that matches how the asset enters a workflow:

| Type | Meaning | Typical catalog surface |
| --- | --- | --- |
| User-invoked | A person chooses the asset for a known problem | A skill or workflow copied into a host |
| Agent-routed | A host or router selects the asset from the task | A workflow contract or router-shaped skill |
| Setup/configuration | The asset audits or stages local configuration | `agent-config` and adapters |
| Reference | A person studies the pattern or uses another project's runtime | External projects and portable references |

The type describes entry into the workflow, not authority to perform side
effects. Approval, verification, and human-acceptance boundaries remain local
to the asset and the adopter's host.

## Minimal adoption record

After a trial, record enough to decide whether the asset earned a place:

1. the friction and task set that motivated the trial;
2. the asset, local equivalent, or combination used;
3. the observable artifact or behavior expected;
4. what happened, including blocked or unknown results;
5. the control or prior behavior used for comparison; and
6. the decision: keep, adapt, replace, or remove.

The [evidence-based improvement reference](workflow-multipliers/evidence-based-skill-improvement.md)
contains a fuller experiment contract. A passing validator proves packaging
and boundary behavior; it does not prove that an asset improves every setup.
