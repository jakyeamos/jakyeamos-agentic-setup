# Jakye Amos Agent Skills

## Portable Agentic Workbench

I turn recurring AI-agent failure modes into portable systems for context
management, workflow routing, safety, evaluation, and durable handoffs.

This repository is a curated, vendor-neutral workbench for agents and the
people evaluating how I adapt AI systems to real work. It packages reusable
workflow contracts and two backward-compatible skills while keeping private
runtime infrastructure, managed vendor configuration, generated harvests,
session stores, and credentials outside the distribution boundary.

## Start here

The catalog is the source of truth:

```bash
python3 scripts/workbench.py list --json
python3 scripts/workbench.py search --query "long context" --json
python3 scripts/workbench.py show context-budget-governor --json
python3 scripts/workbench.py install context-budget-governor \
  --target codex --root /tmp/workbench-target --dry-run --json
```

Read [`AGENTS.md`](AGENTS.md) for the agent mining contract,
[`catalog/index.md`](catalog/index.md) for the human index, and
[`docs/mining.md`](docs/mining.md) for the inspection workflow.

## Curated surfaces

- `context-budget-governor` - checkpoint and compaction policy with a 150,000
  estimated-token hard boundary and a reviewable handoff template.
- `repo-aware-context` - repository-first routing that separates policy, live
  truth, reference, evidence, and handoff context.
- `governed-work-loop` - route -> context -> execute -> verify -> handoff.
- `safe-tool-guards` - dry-run, target, approval, and verification contract for
  shell and tool actions.
- `evaluation-evidence` - sanitized contract fixture and vocabulary for
  observed evidence, hypotheses, and limitations.
- `research-domain-writing` - research -> packet -> draft -> QA -> style skill.
- `terrace` - router skill for Terrace planning, execution, validation, review,
  and release-readiness work.

Codex, Claude, Cursor, Copilot, and generic adapters are available as staged
manual-review mappings. Gemini is cataloged as a reference only in v1 because
this package does not claim stable install semantics for that surface.

## Install safely

Installation requires an explicit target root, defaults to dry-run, copies only
manifest allowlisted files, never overwrites an existing file, and reports
missing dependencies without installing them. Adapter and hook-shaped assets
are staged for review; nothing is silently registered in a real home
configuration.

Apply into a disposable directory after reviewing the plan:

```bash
python3 scripts/workbench.py install context-budget-governor \
  --target generic --root /tmp/workbench-target --apply --json
```

The original copyable skill paths remain available for hosts that do not use
the catalog installer:

```bash
AGENT_SKILL_ROOT=/path/to/agent-skills
mkdir -p "$AGENT_SKILL_ROOT"
cp -R skills/research-domain-writing "$AGENT_SKILL_ROOT/research-domain-writing"
cp -R skills/terrace "$AGENT_SKILL_ROOT/terrace"
```

`research-domain-writing` may use the optional external `rdw` CLI, and
`terrace` requires the external `terrace` CLI. The package never installs
those dependencies for you.

## Validation and clean-room check

Runtime code uses only Python's standard library:

```bash
python3 scripts/validate_skills.py
python3 scripts/validate_catalog.py
python3 scripts/public_safety_check.py
python3 scripts/workbench.py validate
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/pre_cr_coverage.py
```

The tests install into a disposable temporary directory and do not require
Codex, Claude, Cursor, Copilot, Gemini, AIOS, TMCP, Quality Runner, or any
external CLI. The clean-tree `pre-cr run` command may report that no coverage
result was produced when there is no changed diff; run it against a non-empty
feature diff as part of release review.

## Evidence boundary

Case studies explain problem -> mechanism -> evidence -> limitation for
compaction, routing, safety guards, governed execution, and portable skill
distribution. They distinguish observed configuration and command behavior
from hypotheses. No case study claims a model-quality or performance gain
without a measured baseline.

See [`ATTRIBUTION.md`](ATTRIBUTION.md) and [`SECURITY.md`](SECURITY.md) for
provenance, redistribution, and reporting guidance.
