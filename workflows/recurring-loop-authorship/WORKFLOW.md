# Recurring Loop Authorship

Use this workflow to convert a repeated practice into a durable, portable
workflow specification without copying a private setup wholesale.

## 1. Recognize the loop

Capture one representative run, the event or cadence that starts it, the
desired output or state change, and the point at which the run is complete.
If recurrence or completion is not established, ask one question and stop.

## 2. Interview one decision at a time

Resolve the highest-leverage missing field with one question and a recommended
answer. Progress through inputs, execution tools, human checkpoints, failure
and retry behavior, persistence, and readiness. Use the user's notes and
artifacts as evidence; do not infer missing authority.

## 3. Separate portable behavior from adapters

Describe the invariant workflow in generic terms and list schedules, commands,
repositories, destinations, or account roles as replaceable local adapters.
Keep credentials and private runtime state out of the handoff.

## 4. Define the approval boundary

Name the artifact a person reviews, what the person is authorizing, and the
actions that remain human-only. A passing check is evidence, not permission to
send, publish, merge, delete, or submit.

## 5. Define failure and durability

Specify safe retry behavior, duplicate handling, blocked and escalation states,
persistent state, receipts, and logs. Keep unknown policy choices explicit.

## 6. Gate readiness

Declare the spec ready only when an implementer can build without follow-up or
the remaining choices are explicitly non-blocking. Otherwise return the next
single question and its recommended answer.

## 7. Hand off the spec

Return trigger, inputs, steps, output/state, adapters, checkpoints, failure
rules, persistence, verification, and open items. See the [skill contract](../../skills/recurring-loop-authorship/SKILL.md).
