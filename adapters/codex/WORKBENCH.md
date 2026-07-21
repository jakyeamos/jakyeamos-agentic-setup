# Codex adapter

Use the portable workbench as project-level guidance and keep host lifecycle
configuration separate.

- Map `context-budget-governor` to the host's compaction/checkpoint lifecycle
  only after reviewing the threshold and the checkpoint template.
- Keep the 150,000-token value as a policy default, not a promise about a
  particular model's behavior.
- Map `safe-tool-guards` to the host's pre-tool or shell guard surface when it
  is available; stage the mapping for manual review.
- Keep repository instructions, live truth, and handoff artifacts in the
  repository's declared locations.

This adapter contains no host configuration, credentials, session data, or
registration command.
