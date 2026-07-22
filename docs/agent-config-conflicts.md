# Agent-config conflict contract

Conflicts are data, not permission to guess. Record both sources, their owners,
the observed state, the competing behavior, and the proposed precedence. Keep
the source files untouched until the owner explicitly resolves the ledger.

The engine blocks synchronization for unresolved conflicts, unknown live
members, unsupported runtimes, broken links, missing targets, and existing
destination content. It never deletes an unknown live member and never
overwrites an existing file or directory. If any blocking action exists, an
apply run performs no writes at all.

Use `AUDIT_COMPLETE` while the ledger is open. Use `MIGRATION_COMPLETE` only
after the ledger is empty, the route graph is valid, and the post-apply drift
and doctor checks are clear.
