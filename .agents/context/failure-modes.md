# Common failure modes and recovery

- A broken manifest link or duplicate asset ID means the catalog is not
  publishable. Repair the source entry and rerun catalog validation.
- A missing or stale context packet means an agent may guess repository
  boundaries. Refresh the packet and its `last_reviewed` date only when the
  content was actually checked.
- A public-safety finding is a release blocker. Remove or redact the material;
  do not weaken the scanner or add a broad exclusion.
- A destination conflict, unknown live member, or changed baseline blocks
  install/sync. Preserve the destination and review the conflict explicitly.
- An unsupported runtime or missing external CLI is `unverified` or
  `manual-review`, not a successful installation.
- A no-coverage Pre-CR result is a measurement gap. Run the coverage command
  against a real changed diff instead of claiming coverage from a clean tree.

Recovery is: keep the receipt, repair the smallest owned surface, run the full
quality contract, inspect the diff, then commit the coherent change.
