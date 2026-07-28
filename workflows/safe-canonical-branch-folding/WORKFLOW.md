# Safe Canonical Branch Folding

Use this workflow to consolidate named branch work without losing local work
or confusing a local ref with the canonical remote state.

## 1. Scope the transition

Name the repository, canonical target, source branches, remote, required
checks, and which of integration, push, and pruning are authorized. Mark
missing scope `OPEN`.

## 2. Freeze and inventory

Read working-tree status, target/source SHAs, ancestry or patch-equivalence,
local/remote divergence, and existing conflicts. Preserve dirty work. Do not
clean the target just to make the operation easier.

## 3. Classify sources

Create one ledger row per source: integrated, patch-equivalent, unique,
unpublished, absent, or ambiguous. Only the first two can be candidates for
supersession, and even those require evidence and authorized scope.

## 4. Integrate in isolation

Prepare the target transition in a disposable worktree or equivalent isolated
branch. Use the repository's normal merge, cherry-pick, or port method. Stop on
conflicts, unexpected diffs, or newly changed remote state.

## 5. Review and verify

Inspect the history and diff, run the relevant repository checks, and record
verified, blocked, and not-run results separately. Keep human acceptance and
remote publication as distinct states.

## 6. Update and re-read

With explicit authority, update the canonical target and then re-read live
remote refs to verify the intended SHA. If the remote cannot be checked, stop
before claiming completion.

## 7. Prune only after proof

Prune only named refs whose work is proven represented, whose live remote state
agrees, and whose deletion is authorized. Preserve every uncertain ref.

## 8. Hand off the ledger

Return the target before/after SHAs, source classifications, integration
methods, checks, mutations, preserved work, and the next safe action. Include
the mandatory per-source `deletion_authority_recheck` on that next line, even
when no mutation occurred. See the [skill contract](../../skills/safe-canonical-branch-folding/SKILL.md).
