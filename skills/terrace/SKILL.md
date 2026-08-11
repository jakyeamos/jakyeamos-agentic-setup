---
name: terrace
description: Route Terrace workflow intent through the local Terrace CLI. Use when the user mentions Terrace or asks to plan, execute, validate, review, complete, audit, ship, resume, migrate GSD artifacts, manage backlog, inspect rules, map a codebase, or run Terrace phase, quick-task, UI, PRD, preset, corpus, settings, spec, or release-readiness workflows.
---

# Terrace

Use this skill as the single Terrace router. Do not install or publish one skill per Terrace subcommand.

## Default Route

- If the user gives natural-language workflow intent, run `terrace do "$ARGUMENTS"`.
- If the user gives no arguments, run `terrace next`.
- If the user names a precise Terrace action, use `references/commands.md` to choose the matching CLI command.
- Inspect blockers, warnings, generated files, and next-command output before continuing.
- Do not bypass Terrace gates or claim success when Terrace reports blockers.

## Before Running Commands

Check that the CLI is available:

```bash
terrace doctor
```

If the CLI is missing, tell the user to install Terrace from the Terrace project documentation. Do not invent install commands in this skill.

## Completion

Complete only when the selected Terrace command returns a successful state, its
generated files and next-command output have been inspected, and every blocker
or warning has an explicit disposition. If Terrace reports a blocker, stop with
that blocker and the exact next action instead of claiming success.

## Command Reference

Read `references/commands.md` when routing a named Terrace action.
