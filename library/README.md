# Entry library

This directory is the preferred home for newly authored multipliers:

```text
library/<type>/<slug>/
```

Use the type for what the entry is. Put topics and use cases in catalog
metadata rather than nesting the same entry under several topical folders.
The allowed types and their meanings live in
[`catalog/taxonomy.json`](../catalog/taxonomy.json).

Existing assets under `skills/`, `workflows/`, `adapters/`, `fixtures/`, and
other stable paths remain where they are because those paths are part of the
installation contract. The catalog projects both legacy paths and new library
paths into the same entry model.

## Add an entry

1. Choose one type from the taxonomy.
2. Create `library/<type-directory>/<slug>/` and put the native payload there.
3. Add one record to [`catalog/manifest.json`](../catalog/manifest.json).
4. Use `editorial.type` only when the manifest `kind` does not express the
   human-facing type; add `editorial.topics`, `editorial.use_cases`, `why`,
   `use_when`, or `avoid_when` when they improve discovery.
5. Add the entry ID to a taxonomy collection only when it belongs in an
   intentional editorial grouping.
6. Regenerate and validate the human index:

   ```bash
   python3 scripts/workbench.py index --write
   python3 scripts/workbench.py validate
   ```

The validator rejects unknown type directories, library folders without a
manifest record, type/folder disagreement, invalid topic slugs, unknown
collection members, and a stale generated index.
