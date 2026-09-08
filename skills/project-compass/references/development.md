# Development foundation

The Python helper is the canonical producer. Pronto imports its output and
preserves its authority, uncertainty, and source identity. Specifications own
detailed behavior; Telescope owns observed source structure; Quality Runner
owns quality assessment. Compass links those sources to intended outcomes.

## Read-only interfaces

```sh
python3 scripts/project_compass.py family <workspace> --json
python3 scripts/project_compass.py change-context <workspace> --path src/example.py --base HEAD --json
python3 scripts/project_compass.py change-context <workspace> --base <base-sha> --prepared <packet.json> --completion --json
python3 scripts/project_compass.py assess <workspace> --proposal <proposal.json> --json
```

Family (`compass-family/v1`) contains the compatible root summary, nodes,
relationships, continuity, coverage and source digests. Missing, malformed or
unsupported children stay visible. Root scores remain declared maturity;
`current` means a current projection, not verified product behavior. Registry
`active` retains its legacy meaning; it does not ratify new intent.

Change context (`compass-change-context/v1`) binds the exact workspace and base
revision to selected paths, inherited constraints, affected consumers,
contract, binding, decision and relationship revisions, required proof, blockers and drill-down references.
Entry can be eligible to prepare work before proof is recorded. Completion
requires current proof and exits 2 on failure. An unchanged prepared packet is
required to detect scope expansion and concurrent intent changes. Compare the
actual diff including both sides of renames and untracked source files. Receipt
files under `.project-compass/evidence/` are the sole excluded observation output.
Packets above 32 KiB fail explicitly; reduce the scope rather than clip a
constraint. Family output and each source file are bounded to 1 MiB at the
Pronto bridge; oversized data is unavailable, never a partial success.

## Development bindings

`.project-compass/development.json` uses `compass-development/v1`, revision >= 1:

- `inventory`: `source: git-tracked`, explicit `include` glob patterns, and
  `exclude` objects with pattern, reason, and kind `excluded` or `generated`.
  A behavior inventory can link `behavior_ref` to an existing JSON document
  with `behaviors[].id` (including Pronto behavior assurance). Tracked and
  untracked nonignored paths are inspected. Missing declared paths stay visible.
- `bindings`: stable id, compass_id, authority (`accepted`, `proposed`,
  `observed`), exact paths, outcome IDs, behavior IDs, constraints, references,
  dependencies and proof requirements. Accepted bindings require an accepted
  `decision_id`, and draft/retired compasses never count as accepted coverage.
  Directories and guessed prefixes cannot establish path coverage.
- `decisions`: stable id, summary, source, status (`accepted`, `proposed`,
  `superseded`) and optional supersedes ID. Source records the actual decision;
  an agent cannot manufacture acceptance from implementation or a passed test.
- `proof`: requirement id, receipt path, reviewed command argv and canonical
  `oracle_ref`. The explicitly invoked command must match the reviewed argv. References may name a local file
  or JSON Pointer (`file.json#/path/to/behavior`). Broken pointers fail.
  Remote, conversation and non-JSON anchors remain unverified references.

Observations may be updated within task authority. Purpose, exclusions,
compatibility and acceptance changes must cite an existing decision or remain
proposed. Concurrent contract, decision, relationship or accepted-binding changes require revision
reconciliation and a newly prepared packet, never blind replacement. Preserve
superseded decisions and unrelated legacy gaps.

## Source-bound verification

An agent may explicitly run a task-authorized validation command and capture
its result:

```sh
python3 scripts/project_compass.py prove <workspace> --binding <id> --proof <id> --json -- python3 scripts/test_example.py
```

The helper runs the supplied argv without a shell, with a 120-second deadline;
it never executes commands found in a repository contract. The result is a
`compass-evidence/v1` receipt from `project-compass-check/v1`. It captures the
requirement, workspace, relevant contract/binding digests, exact input and
specification digests, command, exit code, timestamp and output digest. Sources
must match before and after execution. A changed declared dependency invalidates
that proof; unrelated edits do not. Receipt files are local verification
observations, not signed attestations or release approval. Command choice and
oracle adequacy still require repository review. Quality Runner remains an
independent required gate; this receipt never substitutes for its release check.

## Modernization assessment

`compass-modernization-proposal/v1` contains paths/compass_ids, base_revision,
problem, expected_benefit, applicable, applicability_reason, evidence_refs,
rollback, and an existing remediation_id. Optional trigger, planned_work_ref,
and defer_reason explain timing. The assessment returns worthwhile_now,
alongside_planned_work, deferred, not_applicable or insufficient_evidence.
Every disposition has `execution_authority: false` and creates no work.
A new model is a reassessment trigger, never evidence of a repository problem.

## Distribution and pilot acceptance

Maintain the public distribution against its `dev` source and reconcile the
installed canonical copy before promotion. Preserve installed-only quiz
selection and evidence-led prompts. The distribution includes one fixture family
also consumed by Pronto, including a draft and invalid child. Installation must
copy all manifest files, then compare hashes and run the helper from the installed
location. A hash match alone does not establish behavior parity.

Required regressions live in `scripts/test_compass_development.py`: legacy
readability, draft/invalid/dangling visibility, shared consumer inclusion,
selective proof invalidation, actual scope changes, concurrent intent changes,
renames, unrelated legacy isolation and inapplicable modernization. Fresh-context
skill dogfood must additionally demonstrate useful bounded orientation without
inventing accepted intent. Pilot gates must be proven before fleet enrollment.

## Pilot completion gate

The two pilot repositories register `compass-development` with Quality Runner.
At task entry save the selected-path `change-context` JSON at
`.quality-runner/compass/prepared.json` in the task-owned worktree. Keep the
original base and packet for completion. `gate <workspace> --json` loads this
packet and runs the same actual-diff completion producer; it never executes
proof commands. A missing packet, affected conflict, scope expansion or stale
required proof returns nonzero. Reconciliation may prepare a replacement packet
only after reviewing the exact changed intent or expanded scope; never silently
rebaseline to make a gate pass. Unrelated legacy gaps remain visible in family.
Use `--prepared <path>` for an explicit alternative packet location.

Regenerate the shared fixture with `python3 scripts/test_compass_development.py
--write-fixture`; the regression suite compares a fresh projection byte-for-byte
after normalizing only fixture workspace identity and time. Copy the fixture to
Pronto's `fixtures/compass/family.json` in the same interface change.

The gate is a required native `qualityCommands` entry in `.pre-cr.json` and is
registered in Quality Runner's repository gate inventory. This does not claim
QR prevention certification: certification requires separate CI evidence and
isolated-snapshot support for task-local packets. Run the native completion
gate and the independent exact-current QR release check; neither substitutes
for the other.
