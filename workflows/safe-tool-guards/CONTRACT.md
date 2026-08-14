# Tool guard contract

An adapter should accept a request shaped like this conceptually:

```json
{
  "action": "read|write|external-mutation|destructive",
  "command": "logical command description",
  "targets": ["explicit target"],
  "dry_run": true,
  "approval": "required|granted|not-required",
  "identity": "resolved repository identity",
  "checkout": "resolved checkout identity",
  "baseline": "protected revision or explicit read-only source",
  "network_policy": "deny|allowlisted",
  "public_projection": "private|aggregate-only"
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
- A dry-run result is explicitly `planned` or `unknown`, never `pass` or
  `fail`; it records the proposed command and its scope without claiming that
  the guarded behavior occurred. Only a later authorized execution may emit
  `pass` or `fail` (or the applicable blocked/unavailable/timeout outcome).
- Credentials are resolved only from an approved keychain or environment
  surface and never appear in arguments, prompts, logs, transcripts, diffs, or
  artifacts.
- Outbound access is denied unless an explicit policy names an allowlisted
  provider or Git operation. Static audits use the deny policy.
- Missing or stale evidence blocks routing and promotion; it is not a reason to
  silently fall back to an older baseline or dump more context.

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
when the executable or local dependency is missing. Use `timeout` when the
allowlisted command started in an available environment but exceeded its
declared execution limit. Persist fixed reason codes and output hashes, never
raw output. Consumers must count only genuine `fail` and `timeout` results as
quality failures; `blocked` and `unavailable` results remain explicit
measurement gaps.

An unsafe baseline is `blocked`, not a permission to repair the primary
checkout. The disposable baseline must be clean, attached, current,
non-prunable, verifiable, and owned by the runtime. Before/after status evidence
must prove that the source checkout was preserved. Any approval-gated path or
public projection must retain a manual review boundary.

This is a contract reference, not a replacement for a host's security policy.
