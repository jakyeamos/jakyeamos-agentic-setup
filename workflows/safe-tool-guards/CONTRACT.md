# Tool guard contract

An adapter should accept a request shaped like this conceptually:

```json
{
  "action": "read|write|external-mutation|destructive",
  "command": "logical command description",
  "targets": ["explicit target"],
  "dry_run": true,
  "approval": "required|granted|not-required"
}
```

Required behavior:

- `dry_run: true` produces a plan and performs no mutation.
- A target outside the declared scope is rejected before execution.
- Existing files are not overwritten unless the host has an explicit,
  separately reviewed overwrite policy.
- Missing dependencies are reported; they are not installed implicitly.
- Hook and configuration changes are staged for review, never registered as a
  side effect of installing a portable asset.
- The result records `status`, `actions`, `verification`, and any
  `partial_failures`.

Repository-specific checks additionally require:

- a resolved repository and checkout identity;
- a clean, attached, current, non-prunable, verifiable baseline before any
  dynamic check;
- a runtime-owned disposable worktree or archive for dynamic checks;
- no provider, deployment, merge, push, or private-runtime-database access;
- before/after status evidence proving the source checkout was preserved;
- public projections that contain aggregates and methodology only, never raw
  prompts, code, diffs, paths, transcripts, credentials, or command output.

Dynamic verification must distinguish an execution failure from an environment
that could not be verified under the guard policy. Use `pass` for a successful
command, `fail` only when an available command exits unsuccessfully, `blocked`
when policy or network-required bootstrap prevents execution, and `unavailable`
when the executable or local dependency is missing. Persist fixed reason codes
and output hashes, never raw output. Consumers must count only genuine command
failures and timeouts as quality failures; blocked or unavailable results remain
explicit measurement gaps.

This is a contract reference, not a replacement for a host's security policy.
