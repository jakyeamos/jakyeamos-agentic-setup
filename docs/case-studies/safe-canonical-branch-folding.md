# Safe canonical branch folding

## Why this was promoted

The source practice treats a “dev fold” as a state transition with evidence,
not as branch cleanup. Its portable advantage is preserving dirty, unique,
unpublished, ambiguous, and remote-divergent work while proving what can be
consolidated and separating integration from publication and pruning.

## Public reduction

The public skill keeps the branch and remote concepts but removes personal
repository names, machine paths, helper commands, live refs, and host-specific
registration. It requires a source ledger, isolated integration, relevant
checks, live remote re-read, and separate authorization for integration, push,
local deletion, and remote deletion. Every `next` line includes a per-source
`deletion_authority_recheck` so proof cannot be mistaken for authority.

## Blind evaluation

The initial clean-room run preserved all unsafe state, but one case expressed
deletion as “blocked” without restating the missing local/remote authority. The
contract was tightened to use canonical authority states and a mandatory
per-source recheck. The final separate judge evaluated three trigger cases and
one non-trigger case:

- Trigger cases: 3/3 passed.
- Non-trigger cases: 1/1 passed.
- Decision: **Promote** as an experimental public skill.

## Evidence boundary

This proves trigger, preservation, and authority behavior for the sanitized
contract. It does not claim that branch folding is appropriate for every team,
that a particular Git policy should be adopted, or that any remote mutation was
performed.
