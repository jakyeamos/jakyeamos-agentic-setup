# Architecture and boundaries

This repository is a public, vendor-neutral workbench with four cooperating
surfaces:

- `catalog/` and `manifest.yaml` define public asset identity, provenance,
  supported targets, routes, and installation policy.
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
