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
Packets use indented JSON when it fits and lossless compact JSON otherwise.
Packets still above 32 KiB fail explicitly; reduce the scope or use the explicit
complete-artifact route below after broad reconciliation. Never clip a constraint.
Family output and each source file are bounded to 1 MiB at the
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

Use [Evidence-backed design assessment](assessment.md) for the v2 proposal,
reviewable decision assumptions, explicit deletion/simplification/retention
alternatives, and observed benefit comparison. Legacy v1 proposals remain readable
but no longer receive a positive recommendation from field/reference checks alone.
The output keeps `compass-modernization-assessment/v1` and adds the versioned
review contract. Every disposition remains advisory with no execution authority.

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

## Bootstrap acceptance and preservation

`family.bootstrap` (`compass-bootstrap/v1`) assesses each subsystem's usable
links: accepted purpose, parent outcomes, exclusions, constraints, canonical
references, behavior IDs and behavior-specific proof. Each behavior inventory
entry supplies `id` and `spec_ref` (a local canonical specification reference).
Each proof may name `behavior_ids` from its binding. A binding with no declared
relationships supplies `handoff_review`, explaining the reviewed boundary;
this is accepted intent and uses that binding's accepted decision provenance.
The helper does not infer that absence of relationships means no consumers.

Coverage has separate `status` for paths and `behavior_status` for behaviors.
An absent behavior inventory is `unknown`; malformed or duplicate IDs are
`invalid`. An empty unmapped list in either state is not measured completeness.
Pronto shows these producer assessments as intent documentation maturity,
separate from Quality Runner's documentation or verification scores.

After reviewing a bounded subsystem's links, opt into affected-scope enforcement
with `"preservation": "compass-preservation/v1"` in development.json. Missing
bootstrap links then block the affected root and subsystem scope. Older contracts
remain readable with explicit advisory gaps; they are not silently enrolled or
promoted. `linked` means traceable intent, not semantic correctness. Review the
oracle against the canonical behavior, including a case where routine tests pass
but a preservation requirement fails. The helper cannot detect an unstated intent
or an oracle that incorrectly blesses a regression.

## Continue an effort across tasks

Keep the original base and previous packet when handing off ordinary work or a
modernization milestone. Extend scope through the same producer:

```sh
python3 scripts/project_compass.py change-context REPO --base ORIGINAL_SHA \
  --prepared PREVIOUS_PACKET --continue --path NEXT_PATH --json
```

Save the output as the next packet only when eligible. This is cumulative: prior
paths and directly affected subsystems remain, prior accepted intent revisions
must still match, and completion compares the whole actual diff against the
original base. Earlier subsystem proof is checked again at completion. Packet
lineage carries the prior packet digest; retain the source packet in the existing
task or remediation handoff. This creates no executor, scheduler, or new queue.
A fresh base is a new effort and must not be used to erase unfinished obligations.
Intent changes require the existing explicit decision/reconciliation workflow;
`--continue` cannot approve them. Base, workspace, and original obligations are
not automatically rewritten on a branch switch or worktree transfer.

Relevant behavior inventory records and canonical specifications participate in
proof freshness. Unrelated behavior additions do not invalidate proof. Upgrading
from the earlier producer requires refreshing receipts to bind this added input.

For initial repository orientation use `family REPO --summary --json`. Its distinct
`compass-family-summary/v1` schema returns counts and at most 20 subsystem gap
summaries (eight reasons each), explicitly marking details omitted. It never
returns shortened path arrays that could be mistaken for full coverage. Use
`change-context --compass-id ID` next; full `family` is deliberate drill-down.

An ineligible packet cannot become a prepared baseline. Continue from the last eligible packet, reconcile changed decisions explicitly, and retain the original base. Active continuity commitments appear in change context and bind affected evidence; optional nonempty `compass_ids` limits their scope, while historical unscoped commitments stay global. Unresolved commitments block affected work. Read commitments alongside root intent and reconcile semantic contradictions; structural validation cannot discover contradictions in prose. Packets predating commitment/behavior revision fields require explicit preparation with the current helper.

## Complete artifacts for broad reconciliation

Ordinary `change-context` output remains bounded to 32 KiB. After reviewing a
legitimate broader scope, use `change-context REPO --path PATH --base ORIGINAL
--packet-output .quality-runner/compass/reconciled.json --json` (repeat `--path`
as needed). This explicitly writes a complete eligible entry packet, limited
to 1 MiB. It refuses existing destinations, traversal, symlinks and ineligible
or completion packets. Inspect the complete file and its digest before adopting
it with `gate REPO --prepared .quality-runner/compass/reconciled.json --json`.
For the default repository gate, explicitly adopt the reviewed file as
`.quality-runner/compass/prepared.json`, preserving the prior file first. The
artifact descriptor is `compass-packet-artifact/v1`, not a prepared context.
No automatic rebaseline or removal of preservation requirements occurs.

An oversized gate result becomes `compass-gate-summary/v1` only after the
producer checks the complete actual diff and every affected obligation. The
summary retains eligibility, all blockers, affected IDs, proof-status counts,
source/base identity, exact prepared-file digest and a canonical full-result
digest (sorted compact JSON plus newline). `detail_omitted` is explicit. If
even the summary exceeds 32 KiB, the command fails with `context-too-large`.
Small gate results retain the existing complete-context schema.

Pronto CLI consumers must forward `--packet-output` without interpreting a
descriptor as intent. They must preserve the distinct gate-summary schema and
nonzero exit status, and use the Python producer for full validation. Older
wrappers that reject these arguments or schemas are unsupported for this route;
use the direct helper until that wrapper is verified. No UI parity is implied.
