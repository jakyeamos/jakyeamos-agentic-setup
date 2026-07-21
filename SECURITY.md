# Security

Skills and workflows are operational instructions for agents. Treat changes to
`SKILL.md`, workflow contracts, adapters, and installer code like code changes.

## Public boundary

Do not add credentials, authorization values, environment files, browser
profiles, private caches, session databases, raw transcripts, AIOS logs,
generated harvest output, or machine-specific configuration. Use a logical
source reference or an external link instead. The catalog's `excluded` class is
the boundary for material that must not be redistributed.

## Installer guarantees

The dependency-free installer:

- requires an explicit target root;
- defaults to dry-run;
- copies only manifest allowlisted files;
- refuses to overwrite existing files;
- reports missing external commands without installing them;
- stages adapters and hook/config mappings for manual review;
- never edits a home configuration or registers a host integration implicitly.

These are package guarantees, not a replacement for host permissions or a
sandbox. Review an adapter before registering it in a host.

## Review checklist

Before merging a new asset, run:

```bash
python3 scripts/public_safety_check.py
python3 scripts/validate_catalog.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

Check provenance, license status, external dependencies, local links, target
support, and evidence limitations. Never claim that an agent became safer or
more capable from a clean validator run alone.

## Reporting

Report a suspected credential exposure, unsafe command contract, private-path
leak, or instruction-priority confusion through the repository's issue
channel. Do not include the suspected secret in the report; describe the file,
line, and redacted pattern instead.
