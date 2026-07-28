# Documentation as principles

Documentation becomes a workflow multiplier when it helps an agent or person
find the authoritative fact, understand why it exists, and notice when the
fact is stale or uncertain. It is a convention for designing a setup, not a
mandatory skill or a second copy of the setup's state.

## The pattern

For every durable fact, choose one canonical home. Let nearby documents carry
the routing pointer, the reason the fact matters, and any local limitation.
They should link to the canonical home instead of maintaining another current
roster or policy copy.

Good canonical homes include a repository-owned configuration file, a schema,
a focused contract, a decision record, or a generated report with a named
producer and freshness rule.

## A portable fact record

When a fact matters across sessions or tools, make these dimensions explicit:

| Dimension | Question |
| --- | --- |
| Statement | What is true, in plain language? |
| Owner | Which file, project, or process is authoritative? |
| Scope | Which repository, host, phase, or audience does it cover? |
| Freshness | When and how is it rechecked? |
| Reason | Why does the rule or fact exist? |
| Consumers | Which workflows need a pointer to it? |
| Evidence | What observation, command, or source supports it? |
| Limits | What is unknown, blocked, manual, or intentionally excluded? |

The record can live in Markdown, JSON, YAML, a database-backed report, or a
different local system. The important property is that the source and its
limits are visible.

## Authoring loop

1. **Inventory the claim.** Search for duplicated instructions, rosters,
   paths, thresholds, and completion statements before editing.
2. **Select the owner.** Prefer the narrowest source that can actually enforce
   or refresh the fact.
3. **Write the reason.** Preserve the non-obvious discovery that prevents a
   future agent from “simplifying” the rule back into a failure mode.
4. **Replace mirrors with pointers.** Keep summaries short and link to the
   owner; do not create a second live configuration surface.
5. **Add freshness and uncertainty.** Mark stale, blocked, manual-review, and
   unknown states instead of letting an old positive sentence survive.
6. **Check the consumers.** Confirm that each routed reader can reach the
   owner without loading an entire unrelated corpus.
7. **Recheck after change.** Validate links, schemas, commands, and the
   owner-to-summary relationship as part of the relevant quality gate.

## Useful handoff prompt

An adopter can hand this idea to an agent without copying this repository's
structure:

> Find duplicated claims about this workflow. For each claim, identify the
> narrowest authoritative owner, explain why it exists, list the consumers,
> and mark freshness or uncertainty. Propose pointer-only documentation
> changes. Do not overwrite conflicting sources or declare migration complete
> until the conflict ledger is empty.

The prompt is an idea to customize, not a universal command. The agent still
needs the adopter's repository scope, approval boundary, and verification
commands.

## Anti-patterns

- A README repeats the current command roster from a configuration file.
- A generated report is treated as source truth without naming its producer or
  freshness rule.
- A provider-specific projection is mistaken for the portable policy.
- A missing or stale source is summarized as if it were a passing result.
- A migration removes the old source before conflicts and consumers are
  accounted for.
- A “complete” handoff contains conclusions but no owner, evidence, or next
  stopping condition.

## Relationship to the workbench

This convention complements [`repo-aware-context`](../../workflows/repo-aware-context/WORKFLOW.md),
[`low-always-loaded-instruction-migration`](../../skills/low-always-loaded-instruction-migration/SKILL.md),
and [`evaluation-evidence`](../../workflows/evaluation-evidence/WORKFLOW.md).
Use those assets if they fit; a setup can implement the same principles with
its own documentation and tooling.
