# Safe shell and tool guards

Use this workflow before an agent executes a shell command, writes a file, or
calls a tool with side effects.

1. Classify the action as read-only, reversible write, external mutation, or
   destructive operation.
2. Resolve the exact target paths and arguments.
3. Check the repository or tool's dry-run surface.
4. Present or record the proposed action when approval is required.
5. Execute only the approved scope.
6. Verify the result and record any partial failure.

For repository checks, resolve the identity and checkout first. A dirty,
detached, stale, prunable, or unverifiable baseline is a blocked target, not a
permission to improvise. Materialize a protected revision into a disposable
directory owned by the runtime; never run an audit by changing the primary
checkout. Compare its status before and after any read-only preparation pass.

The baseline gate is explicit: record the normalized repository identity,
checkout path, branch, HEAD, common Git directory, and local freshness evidence
before execution. A missing fetch or remote observation makes remote freshness
`unknown`; it does not justify treating an old local ref as current. Refuse
detached, dirty, stale, prunable, or unverifiable sources and create a fresh,
runtime-owned disposable worktree from a protected revision instead.

Do not dump an entire repository into an agent context or an artifact. Pass
only the files required by the task, and redact prompts, code, diffs, private
paths, transcripts, credentials, and raw command output from public or shared
projections. Static audits should not contact providers, deploy, merge, push,
or access a private runtime database.

Default outbound access is denied. A bounded execution may allow only the
provider or Git operation explicitly named by its policy, and a static audit
allows neither. Credentials may come from an approved keychain or environment
surface only; never pass them in command arguments, prompts, logs, transcripts,
diffs, or artifacts. Migrations, dependency and lockfile changes, auth,
security policy, CI, deployment, secrets, generated files, deletions,
instructions, and public outputs are approval-gated even when a tool proposes
them as low-risk.

Use the minimum-context contract: load the nearest instructions and context
index, then live truth, then routed references. Missing or stale context blocks
routing and promotion; it must not trigger a silent fallback or a whole
repository dump.

The guard must reject unresolved home-directory globs, implicit configuration
registration, credential-bearing arguments, and destructive operations whose
target cannot be identified exactly. It should preserve a safe fallback when a
host-specific hook or guard is unavailable.

Adapters may translate this contract to a host's pre-tool or shell-hook
surface, but they must be staged for manual review. Every promoted guard rule
must name an owner, executable validation, supported targets, and a removal condition.
The shared result taxonomy includes `pass`, `fail`, `blocked`, `unavailable`,
and `timeout`; preserve those distinctions when translating to a host surface.
This package does not ship a guard binary or silently edit host configuration.

The [environment-legibility audit](../environment-legibility-audit/WORKFLOW.md)
uses this contract when it inspects repositories and generates remediation
plans.

See the [guard contract](CONTRACT.md) and the [safety case study](../../docs/case-studies/safety-guards.md).
