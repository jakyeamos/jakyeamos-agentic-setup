# Repo-aware context routing

Use this workflow before an agent searches broadly, edits a repository, or
recommends an installation.

## Route

1. Identify the exact repository and branch in scope.
2. Read the nearest operating instructions and local context index.
3. Read the live truth file if one exists; treat it as a snapshot, not a
   historical log.
4. Search for an existing implementation before adding a helper or surface.
5. Select only the context needed for the current task.
6. State assumptions when a missing artifact could change the design.

## Context layers

Keep these layers separate:

- **Policy:** instructions that govern the agent.
- **Truth:** current branch, status, tests, blockers, and next action.
- **Reference:** stable architecture, contracts, and examples.
- **Evidence:** command output, test results, and review findings.
- **Handoff:** the compact state needed by the next agent or session.

Do not treat a generated index, an old report, or the mere presence of a file
as proof that the behavior is current. Verify behavior at the narrowest useful
surface.

## Scope guard

Do not scan a home directory or a multi-repository workspace by default. Ask
for an explicit boundary or use the repository's declared source map. Public
catalogs should contain logical source references rather than machine paths.

The [governed work loop](../governed-work-loop/WORKFLOW.md) is the execution
companion to this routing discipline. The [context-routing case study](../../docs/case-studies/context-routing.md)
records what is observed, what is inferred, and what remains unmeasured.
