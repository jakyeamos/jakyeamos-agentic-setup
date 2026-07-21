# Mining the workbench as an agent

This repository is designed to be inspected by an agent without loading a
private infrastructure tree.

## Recommended sequence

1. Read `AGENTS.md` and the human catalog index.
2. Run `python3 scripts/workbench.py validate` to establish the public boundary.
3. Run `list --json` and filter by capability or target.
4. Run `search --query "<problem>" --json` for a focused candidate set.
5. Run `show <asset-id> --json` for the complete provenance, evidence, and
   install record.
6. Read only the listed entrypoint files and evidence references.
7. Produce a recommendation with mechanism, evidence, dependencies, and
   limitation.
8. If installation is requested, run the dry-run with an explicit disposable
   root. Apply only after the plan is reviewed.

## What to trust

The manifest is authoritative for what is packaged. A `portable` record can be
copied under its declared mode. An `adapter` is target-specific and must be
staged. A `case-study` explains a design or evidence trail. An `external`
record is a link, not a dependency that the installer fetches. An `excluded`
source is a boundary warning.

Case studies use four labels:

- **Problem:** the failure mode or operational cost.
- **Mechanism:** the repeatable behavior proposed here.
- **Evidence:** an observation or reproducible local check.
- **Limitation:** what has not been measured or what depends on a host.

Do not convert a hypothesis into a performance claim. A clean validation run
proves package integrity, not improved model quality.

## Safe installation

The installer never chooses a home configuration directory, installs a missing
dependency, overwrites a target file, or registers a hook. It reports missing
commands and stages manual adapters. A clean-room agent can therefore inspect
and test the package with only Python's standard library.
