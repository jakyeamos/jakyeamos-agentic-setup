# Packaging and rollback

This repository is a public source catalog and setup engine; it does not
deploy a service or register a host automatically. Release preparation is a
reviewed validation pass followed by an atomic commit and push to `dev`.

Inspect the manifest, run the full quality contract, review public-safety
output, and stage any adapter or installer destination manually. Do not
publish a registry artifact or modify a home configuration as part of tests.

Rollback is a normal `git revert` of the atomic commit. Remove only generated
`.pre-cr/`, `audit/`, `dist/`, or local state artifacts when they are not
evidence; never rewrite history or delete unresolved conflict records to make
validation pass.
