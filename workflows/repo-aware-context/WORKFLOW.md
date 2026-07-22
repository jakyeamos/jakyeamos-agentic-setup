# Repo-aware context routing

Use this workflow before an agent searches broadly, edits a repository, or
recommends an installation.

## Route

1. Identify the exact repository and branch in scope.
2. Resolve the repository identity before broad discovery: normalize its
   remote when present, record its common Git directory, and distinguish each
   checkout or linked worktree state.
3. Read the nearest operating instructions and local context index.
4. Read the live truth file if one exists; treat it as a snapshot, not a
   historical log.
5. Search for an existing implementation before adding a helper or surface.
6. Select only the context needed for the current task.
7. State assumptions when a missing artifact could change the design.

## Environment evidence

When auditing or preparing a repository, check the context index, linked local
documents, command references, and their freshness. A file's presence is not
evidence that an instruction is routed, executable, or current. Record broken
links, missing owners, stale commands, and unverifiable baselines explicitly.
Use `unknown`, `stale`, or `blocked` when evidence is incomplete.

Dynamic command checks must run only from a runtime-owned disposable baseline.
Refuse dirty, detached, stale, prunable, or otherwise unverifiable checkouts,
and compare the original checkout status before and after the check.

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
