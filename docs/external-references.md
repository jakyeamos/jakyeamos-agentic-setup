# External reference map

This page links the public projects that inform or complement the workbench.
They remain separately owned systems: this repository does not vendor their
runtimes, generated outputs, credentials, private state, or host registration.

AWL may promote a separately owned public project here as a reference-only JAS
asset when the project explains a meaningful part of the author's workflow or
developed advantage. The admission record must remain link-only and manual
review; portable behavioral patterns can be promoted separately when they pass
the normal evidence and redaction gates.

| Project | Reusable advantage | Use it when… | Boundary |
| --- | --- | --- | --- |
| [TMCP](https://github.com/jakyeamos/tmcp) | Compiles a natural-language objective into a task-specific packet, routes from current skills and evidence, recompiles as the task changes, and leaves an audit trail. | You want adaptive packet composition or workflow routing around the portable contracts. | TMCP runs from its own project or package; the workbench keeps only portable boundary patterns. |
| [Pronto](https://github.com/jakyeamos/pronto) | Local-first portfolio command center for repository and worktree discovery, structured quality evidence, provider-neutral snapshots, and read-only remediation or release previews. | You want a human-facing surface over repository state and evidence without granting mutation authority. | Pronto is a separate application; no desktop runtime, database, or private feed is copied here. |
| [Pre-CR Suite](https://github.com/jakyeamos/pre-cr-suite) | One project-owned `.pre-cr.json` contract can drive editor integrations and a headless changed-line readiness gate. | You need project-local coverage and pre-review parity across supported clients. | Pre-CR is an optional verifier; the workbench does not require its CLI or editor clients. |
| [Quality Runner](https://github.com/jakyeamos/quality-runner) | Evidence-first repository and fleet assessment that produces bounded findings, remediation plans, and a validated maturity-feed boundary. | You need quality evidence or a redacted feed for another local consumer. | Quality Runner owns its runtime and artifacts. Its reports do not authorize fixes or publication by themselves. |
| [AIOS](https://github.com/jakyeamos/AIOS) | Durable local orchestration, session/context infrastructure, and report-oriented workflow state. | You already use AIOS for local coordination and want to map portable contracts into it. | AIOS storage, hooks, databases, session state, and generated harvests stay external. |
| [Agent Eval Contract](https://github.com/jakyeamos/agent-eval-contract) | Provider-neutral records for cases, rubrics, evidence, and agent-run results. | You need a stable record contract independent of the evaluator runtime. | The workbench does not copy private evaluation data or provider clients. |
| [Agent Eval Runtime](https://github.com/jakyeamos/agent-eval-runtime) | Report-only local execution, comparison, and benchmark-evidence collection. | You need an execution runtime for the evaluation contracts. | Runtime behavior and evaluation artifacts remain in that project. |
| [Context Compiler Contract](https://github.com/jakyeamos/context-compiler-contract) | Typed contracts for context selection, routing manifests, and receipts. | You are building or adapting a context compiler. | The contract is linked for integration; source selection and compilation remain external. |

## Optional relationships

These relationships explain the wider workflow without prescribing a stack:

- TMCP can compile or route the portable workbench assets when an adopter uses
  TMCP; it is not a prerequisite for any catalog entry.
- Quality Runner owns the validated maturity feed, and Pronto is a downstream
  consumer of that feed. The workbench links the relationship without copying
  the feed or its private path.
- Pre-CR can provide a project-local readiness verifier for an adopter that
  already uses the `.pre-cr.json` contract.
- Agent Eval Contract and Agent Eval Runtime can supply a record format and
  execution harness for the evidence loops described here.
- AIOS can provide durable local orchestration, but the portable contracts are
  intentionally useful without it.

Choose projects independently. A link is a discovery aid, not an install
instruction or a claim of runtime compatibility.
