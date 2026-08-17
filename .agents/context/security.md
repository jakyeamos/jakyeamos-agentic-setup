# Security and approval constraints

The public boundary excludes credentials, private paths, environment files,
browser profiles, session databases, transcripts, generated harvests, and
host-managed registration files. Use logical source references or external
links instead of copying private material.

The installer requires an explicit target root, defaults to dry-run, refuses
overwrites and unknown live members, and stages adapters for manual review.
Successful copy/stage applies write an installer-owned receipt under the
target's `.workbench-receipts/` directory. Receipt-scoped `uninstall` also
defaults to dry-run and removes only exact recorded files whose contents still
match the receipt; missing receipts, modified files, symlinks, and unknown
manifest targets block removal, while unrelated members are preserved. It
must not automate login, MFA, CAPTCHA, credential collection, provider calls,
or host registration. Validation must not use network access or AIOS.

Protected operations include `--apply`, sync to a live destination, publishing,
deployment, migration, remote writes, and any action involving credentials.
If a guard or provenance check is unavailable, stop with a visible blocked
result and preserve the source tree.

Run `python3 scripts/public_safety_check.py` before merging public assets. It
must reject private path patterns, credential-shaped values, unsafe database
artifacts, and distributable environment or key files.
