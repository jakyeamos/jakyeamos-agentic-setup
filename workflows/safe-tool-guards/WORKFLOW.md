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

Do not dump an entire repository into an agent context or an artifact. Pass
only the files required by the task, and redact prompts, code, diffs, private
paths, transcripts, credentials, and raw command output from public or shared
projections. Static audits should not contact providers, deploy, merge, push,
or access a private runtime database.

The guard must reject unresolved home-directory globs, implicit configuration
registration, credential-bearing arguments, and destructive operations whose
target cannot be identified exactly. It should preserve a safe fallback when a
host-specific hook or guard is unavailable.

Adapters may translate this contract to a host's pre-tool or shell-hook
surface, but they must be staged for manual review. This package does not ship
a guard binary or silently edit host configuration.

See the [guard contract](CONTRACT.md) and the [safety case study](../../docs/case-studies/safety-guards.md).
