---
name: recurring-loop-authorship
description: Use when a repeated personal routine should become a customizable workflow specification with explicit state, human checkpoints, retries, and a safe stopping condition.
---

# Recurring Loop Authorship

Use this skill to turn a repeated practice into a workflow another person or
agent can implement and customize. The output is a durable specification, not
a forced copy of the author's setup. Treat the user's examples and notes as
source material; do not fill gaps with invented tools, permissions, or
accounts.

## Trigger

Invoke when one or more of these is true:

- The user describes a recurring manual loop and wants an agent workflow,
  automation design, or reusable prompt for it.
- A routine must survive interruption, delegation, retry, or a later resume
  without losing its contract or artifacts.
- A workflow needs explicit human checkpoints before consequential actions.

## Do not trigger

Do not use this skill for:

- A one-off script or bounded task with fixed inputs and no recurring state.
- Implementing a workflow whose trigger, outputs, tools, checkpoints, failure
  behavior, and acceptance are already complete.
- Prompt wording or documentation polish with no repeated behavior to model.

## Authorship contract

1. **Interview in small steps.** Identify the current stage and ask exactly one
   highest-leverage question at a time. Each question may close only one spec
   dimension; do not bundle retry, persistence, authority, and escalation
   decisions into a disguised questionnaire. Give a recommended answer when
   the evidence supports one. Do not dump a questionnaire or pretend a full
   spec exists after one reply.
2. **Capture the loop.** Record the recurrence or trigger, representative
   inputs, desired output or state change, and what makes the run complete.
3. **Make execution legible.** Name the tools, files, systems, and account
   roles involved at the category level. Keep credentials, login state, and
   private runtime details out of the specification.
4. **Preserve human control.** Identify checkpoints, the brief or artifact a
   person reviews, and which actions must remain human-approved. Verification
   does not equal acceptance, publication, sending, or submission.
5. **Design failure behavior.** Specify retries, idempotency or duplicate
   handling where relevant, escalation, blocked states, persistent state, and
   logs. Do not silently choose a retry policy for a side effect.
6. **Make it customizable.** Separate portable behavior from local adapters,
   commands, schedules, and destinations. Mark assumptions and unresolved
   choices as `OPEN` with what unblocks them.
7. **Check readiness.** The workflow is ready only when an implementer can
   build it without follow-up questions, or every remaining question is an
   explicit non-blocking choice. Otherwise stop at the current question.

## Safety boundaries

Do not invent a recurrence, desired state, tool access, account authority,
credentials, approval, or successful run. Do not authorize outbound
communication, destructive changes, publication, or submission merely because
the loop is recurring. Keep a human checkpoint at the boundary the user has
not delegated. If the supplied notes are thin, interview before drafting a
complete workflow.

## Output contract

Until the spec is ready, return:

```text
stage: <capture | inputs | execution | checkpoints | failure | persistence | readiness>
known: <facts and current spec fields>
question: <exactly one highest-leverage question>
recommended_answer: <best-supported default, or OPEN>
open: <remaining blocker and what unblocks it>
```

When ready, return a portable workflow specification containing:

```text
trigger: <event or cadence>
inputs: <required inputs and provenance>
steps: <bounded execution stages>
output_or_state: <artifact or state transition>
tools_and_adapters: <portable categories plus local substitutions>
human_checkpoints: <review artifact, authority, and stop boundary>
failure_retry_escalation: <retry, duplicate, blocked, and escalation rules>
persistence_and_logs: <durable state, receipts, and retention>
verification_and_done: <checks and acceptance boundary>
open_items: <none, or explicit non-blocking choices>
```

## Stopping condition

Stop after the one-question turn when the next answer is required to make the
workflow implementable or safe. Stop with an `OPEN` field when the user has
not supplied authority, a destination, or a policy that changes the loop. A
customizable spec may leave local adapters open; it may not hide safety or
completion gaps.
