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

This is a contract reference, not a replacement for a host's security policy.
