---
name: research-domain-writing
description: Research-grounded domain writing pipeline for accurate domain-specific copy. Use when producing jargon-heavy or knowledge-heavy writing in areas like sports analytics, music criticism, technical writing, policy, finance, medicine, or academic work, especially when facts, terminology, source notes, and QA matter more than generic style polish.
---

# Research Domain Writing

Use this skill when the user needs grounded domain copy, not just smoother prose.

## Core Rule

Research and QA happen before style. The humanizer/blader stage may improve rhythm, voice, and clarity, but it must not add facts.

## Pipeline

Run these stages in order:

1. Read `config/router-inference.yaml` and `prompts/domain-router.md`; infer domain, entity, output type, audience, depth, and any explicit overrides.
2. Read `prompts/research-planner.md`; make a focused research plan unless a fresh packet already exists.
3. Read `prompts/researcher.md`; gather facts with available tools and save reusable notes as `knowledge/<domain>/*.yaml` when the host project has a knowledge directory.
4. Read `prompts/knowledge-packet-builder.md`; assemble the evidence and terminology the copywriter may use.
5. Read `prompts/domain-copywriter.md`; draft from the packet only.
6. Read `prompts/domain-qa.md`; fail the draft if facts, jargon, uncertainty, or audience fit are weak.
7. Read `prompts/humanizer-blader.md`; apply style only after QA passes.

For multi-task runs, read `prompts/batch-runner.md` and use `examples/batch-tasks.yaml` as the input shape.

## Defaults

- Infer missing routing fields from the user's request when the intent is clear.
- Ask only when a missing field would materially change research or output.
- Use `config/style-profile.yaml` for voice.
- Use `config/domains.yaml`, `config/output-formats.yaml`, and `config/research-sources.yaml` as the local vocabulary.
- Return to research when the packet is thin, stale, or uncertain.

## Optional CLI

If the `rdw` CLI is installed, prefer it for deterministic validation and prompt-bundle planning:

```bash
rdw doctor
rdw task plan --request "<user request>" --out .rdw-runs/<slug>
rdw batch plan examples/batch-tasks.yaml --out .rdw-runs/<slug>
```

The CLI does not replace the agent. The agent still performs the research, writing, QA, and final application work.

## Completion

Complete only when the draft is bounded by the assembled evidence packet,
domain QA passes for facts, terminology, uncertainty and audience fit, style is
applied after QA, and any remaining unsupported claim or stale source is named.

## References

- `references/limitations.md`
