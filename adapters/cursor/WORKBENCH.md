# Cursor adapter edge

This is sanitized, staged guidance for Cursor. It is not a live host settings
file, project rules file, hook, or registration recipe.

- Route to `repo-aware-context` and `governed-work-loop` only when the task
  matches their triggers.
- Stage context-budget and tool-guard mappings rather than registering them.
- Keep host-managed instructions and generated settings outside the package.
- Verify the mapped workflow in a disposable repository before live use.

This adapter is a behavioral mapping, not a copy of host-managed settings.
