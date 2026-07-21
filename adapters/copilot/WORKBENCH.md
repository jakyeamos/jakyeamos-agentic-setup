# Copilot adapter

Use the portable workbench as repository guidance and keep integration narrow.

- Map the route -> context -> execute -> verify -> handoff loop into the
  repository's reviewed agent instructions.
- Use the safe-tool-guards contract for any shell or tool integration that the
  host supports.
- Treat Gemini-like or other unverified host surfaces as references until the
  host documents a stable installation contract.
- Record a handoff and run the repository validation command after mapping.

No managed Copilot configuration or external guard executable is redistributed.
