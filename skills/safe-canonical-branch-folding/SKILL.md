---
name: safe-canonical-branch-folding
description: Use when named feature branches need to be folded into a canonical development line with dirty-state preservation, remote-truth checks, explicit approval, and reversible verification.
---

# Safe Canonical Branch Folding

Use this skill when work needs to be consolidated into a named canonical
development branch. Treat branch folding as a reviewed state transition, not
as generic branch cleanup. The canonical target may be called `dev`, but the
caller must name it.

## Trigger

Invoke when one or more of these is true:

- The user explicitly asks to fold, merge, port, or consolidate named source
  branches into a named development line.
- Completed work is distributed across branches and the user wants the
  canonical line synchronized.
- The user asks to remove source references after proving that their work is
  represented on the canonical line.

## Do not trigger

Do not use this skill for:

- An ordinary edit or commit on the current branch.
- A vague request to delete old branches, prune everything, or make the
  repository tidy without named sources and a target.
- A release or production merge when release authorization and policy have
  not been stated.
- Any operation that would require guessing whether unique, dirty, unpublished,
  or ambiguous work is disposable.

## Inputs

Collect or mark `OPEN` for:

- Repository and canonical target branch.
- Explicit source branch list and remote, if relevant.
- Whether local integration, remote push, and reference deletion are each in
  scope.
- Repository branch policy, required gates, and the acceptable integration
  method.

Never infer mutation authority from the existence of a branch or from a
cleanup-sounding request.

## Folding contract

1. **Inventory before mutation.** Read the working-tree status, local and
   remote refs, target and source commits, and current remote target. Preserve
   dirty work and identify divergence instead of assuming the local target is
   canonical.
2. **Classify every source.** Record whether each source is integrated,
   patch-equivalent, unique, unpublished, absent, or ambiguous. A source with
   unique or unexplained work is preserved and reported, not silently folded or
   deleted.
3. **Prove the proposed transition.** Record target and source SHAs, ancestry
   or patch-equivalence evidence, remote divergence, and the reason the chosen
   integration method is safe. A clean status alone is not proof of
   equivalence.
4. **Integrate in isolation.** Use a disposable worktree or equivalent
   isolated branch for merge, cherry-pick, or port work. Stop on conflicts and
   keep the conflict visible. Do not rewrite source history to make the proof
   easier.
5. **Review and verify.** Run the repository's relevant checks and review the
   resulting diff and history. Distinguish verified integration from human
   acceptance and from remote publication.
6. **Stabilize the target only with authority.** Update or push the canonical
   target only when that exact mutation is in scope. Re-read live remote state
   after a remote write and verify that it equals the intended result.
7. **Prune only proven superseded refs.** Delete no local or remote reference
   until the source's work is proven represented, the live remote agrees, and
   deletion is explicitly authorized. Proof of representation never implies
   deletion authority. Use normal recoverable deletion; never force-push or
   use broad deletion to resolve uncertainty.

## Safety boundaries

Do not use force-push, broad `ours`/`theirs` resolution, history rewriting,
unreviewed remote writes, destructive branch deletion, credential handling, or
external communication to make the fold appear complete. Do not modify a
dirty canonical target to manufacture a clean starting point. If a required
proof, approval, or live ref check is unavailable, stop with the work
preserved.

## Output contract

Return a compact folding ledger:

```text
status: <audited | ready | blocked | complete>
target: <canonical branch and before/after SHA, or OPEN>
sources: <one row per named source: classification, method, evidence>
preserved: <dirty, unique, unpublished, ambiguous, or unrelated work left alone>
changes: <local and remote mutations actually performed, or none>
authorization: <integration, push, local deletion, and remote deletion separately; each is granted, missing, or not requested>
gates: <checks, review, and live remote verification with honest results>
next: <remaining approval, conflict, or safe follow-up>; deletion_authority_recheck: <one row per source: local=<granted | missing | not requested>, remote=<granted | missing | not requested>>
```

Use only the canonical authority states `granted`, `missing`, and `not
requested`; a requested-but-blocked mutation is `missing`. For every requested
deletion, state local and remote deletion authority separately in
`authorization`. The `deletion_authority_recheck` is mandatory on every
`next` line, including blocked and non-mutating audits. It must repeat each
source's local and remote authority with the canonical states; for example:
“feature/search: local=missing, remote=not requested.” Do not replace an
authority state with proof language such as “blocked until represented,” and do
not let proof or a cleanup request stand in for authority. Do not call a fold
complete when a source remains ambiguous, the target was not verified against
live remote state, or a required gate was not run.

## Stopping condition

Stop when the inventory exposes dirty or unique work, a conflict, remote
divergence, missing authority, or an unverifiable equivalence claim. Leave the
classification and safest next action visible; do not resolve uncertainty by
deleting or overwriting state.
