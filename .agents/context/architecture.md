# Architecture and boundaries

This repository is a public, vendor-neutral workbench with four cooperating
surfaces:

- `catalog/manifest.json` defines public asset identity, provenance, supported
  targets, routes, and installation policy; `catalog/taxonomy.json` defines
  the editorial type system and curated collections; `catalog/index.md` is a
  generated projection of both.
- `library/<type>/<slug>/` is the preferred home for new entries. Existing
  `skills/`, `workflows/`, `adapters/`, and fixture paths remain stable install
  interfaces and project into the same entry model.
- `skills/` and `workflows/` contain portable on-demand behavioral contracts;
  `adapters/` contains host-shaped guidance that is staged for review.
- `bin/`, `src/`, and `schemas/` implement the dependency-light Node manifest
  engine and its portable schema.
- `scripts/`, `test/`, and `tests/` validate public safety, catalog structure,
  workflow contracts, and runtime behavior.

The public data flow is:

`authored or sanitized source -> manifest validation -> reviewable staging`

AIOS, private agent configuration, session state, credentials, generated
harvests, host registration, provider calls, and live deployment are outside
this repository. No public asset may require a private path or runtime store.
