# Generic adapter

Map the portable workbench assets to the host's documented project-instruction
and hook surfaces.

1. Install portable workflows into an explicit, disposable target root first.
2. Copy the workflow content into the host's project instruction surface only
   after review.
3. Use the context-budget governor as a policy request or checkpoint command;
   do not assume the host exposes token counts.
4. Stage any hook or guard integration and ask the operator to register it.
5. Re-run the catalog validator and the host's own smoke test after mapping.

The generic adapter has no host-specific registration command and no external
runtime dependency.
