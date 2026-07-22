# Evidence-Backed Change Surface Mapping

Use this workflow to discover likely downstream surfaces of a change while keeping inference bounded, inspectable, and advisory.

## 1. Establish identity

Separate repository identity from the current checkout, revision, branch, and working-tree state. Record the evidence source and freshness for every claim. A name match alone is not identity evidence.

## 2. Map bounded surfaces

Inspect declared ownership, direct imports or references, configured integrations, recent history, and explicit dependency metadata. Add edges only when supported by evidence. Preserve unknown paths and ambiguous references rather than converting them into positive matches.

Each observation should include `surface`, `relation`, `evidence`, `confidence`, `freshness`, `provenance`, and `status`. Keep inferred edges below a declared cap and mark the result truncated when the cap is reached.

## 3. Explain the result

Report confirmed surfaces separately from inferred, stale, unknown, and excluded surfaces. Include the queries or commands used, the revision boundary, the cap, and the reason any result may be incomplete. A zero-result map means “no supported evidence found,” not “no consumers exist.”

## 4. Keep the map advisory

The map may inform review scope, test selection, or a change packet. It must not automatically edit consumers, delete branches, close issues, or claim release readiness. Re-run it after a meaningful revision or when freshness expires. Define a removal condition for temporary adapters and inferred edges.

See [the skill contract](../../skills/evidence-backed-change-surface-mapping/SKILL.md).
