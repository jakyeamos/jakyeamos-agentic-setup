---
name: unknowns-first-exploration
description: Use when an ambiguous task, unfamiliar territory, or tacit preference should become a four-quadrant map that the user can react to before implementation hardens.
---

# Unknowns-First Exploration

Use this skill to turn an underspecified task into a shared map. The map is
the deliverable of exploration; implementation is a separate task that starts
from it. Prefer concrete evidence and artifacts that let the user react over
abstract questions that ask them to imagine a finished solution.

## Trigger

Invoke when one or more of these is true:

- The request is ambiguous, cross-cutting, or likely to hide decisions with
  different architectural consequences.
- The territory is unfamiliar, a reference implementation is being adapted,
  or the user says they will know the right direction when they see it.
- Starting implementation would harden a product, interface, workflow, or
  data decision before the user has reacted to a concrete option.
- A prior attempt exposed surprises and the next attempt needs a map of
  conventions and landmines.

## Do not trigger

Do not use this skill for:

- A bounded one-file task with settled inputs and explicit acceptance.
- A routine answer, command, or diagnosis whose next action is already clear.
- Implementation of a reviewed plan when no unresolved decision is being
  explored.

## Exploration contract

Walk one stage at a time and keep the map visible:

1. **Known knowns.** Scan the relevant territory before speaking. Open with
   settled facts, file-backed constraints, decisions already made, assumptions
   marked as assumptions, and the three quadrants still to walk. Disclose any
   load-bearing finding immediately. If the territory is not available, remain
   at this stage and ask one exact scope or access question, or show a clearly
   labeled proposed scan manifest; do not report future inspection as the
   user's reaction. End this stage with exactly one concrete, high-blast-radius
   user-reaction question about who will use the result, where it runs, or what
   counts as done. Do not advance until that reaction is answered; do not
   replace it with several broad questions or a generic offer.
2. **Known unknowns.** Inventory the questions that can block the task. Resolve
   one at a time in descending architectural blast radius, with a recommended
   answer and short options. Close each in front of the user as answered by
   the user, answered by the territory, or explicitly `OPEN` with its unblocker.
3. **Unknown knowns.** Put a concrete artifact in front of the user: a real
   sample, table, design direction, vocabulary ladder, or disposable mock.
   Probe who consumes it, where it runs, and what done means to its inheritor.
   Record the tacit constraints extracted from the reaction.
4. **Unknown unknowns.** Sweep every file or surface the task will touch and
   state the coverage. Report landmines, unwritten conventions, dead or
   half-built attempts, and inherited findings as cards with evidence, why
   they bite, and what they change. Worst risks come first.
5. **Hand over the map.** Only after stages 1 through 4 have actually been
   completed in order, produce one self-contained artifact with all four
   quadrants, the decision ledger, extracted context, landmine cards, open
   items and their unblockers, a tweakable plan sorted by judgment calls, and
   a copyable implementation prompt. A visible `OPEN` item is allowed in the
   final map; skipping a stage is not.

After the walk, record implementation deviations as new map entries. Before
shipping, package the map with the prototype/spec and review ownership. Before
merging a long or inherited change, use a mental-model quiz to expose what
still was not understood.

## Interaction boundaries

- Ask no more than one decision question at a time in the known-unknowns
  stage; assemble the next reply from the user's answer.
- If the territory can answer a question, inspect it and show the evidence
  instead of asking the user to guess.
- When the territory is unavailable, the stage-1 `reaction` must be one exact
  scope/access question or a clearly labeled proposed scan manifest. “Inspect
  these surfaces first” is queued work, not a reaction.
- Disclose early findings; do not save a load-bearing landmine for the end.
- Label observations, assumptions, hypotheses, and invented examples
  separately. Cite real files or artifacts for factual claims.
- If a scan has not occurred, say so and keep the claim an assumption or
  hypothesis. Do not manufacture a generic landmine card and present it as a
  finding from the target territory.
- The `reaction` field must contain the concrete artifact or exact one question
  the user can react to now. “Present an artifact later” is not a reaction.
- Do not silently close a user judgment, implement before the required
  reaction, or claim the map is complete while required decisions remain
  open.

## Output contract

During the walk, return:

```text
stage: <known-knowns | known-unknowns | unknown-knowns | unknown-unknowns | handoff>
evidence: <file-backed facts and current map delta>
queued: <remaining named questions or sweep work>
reaction: <one question or one concrete artifact for the user to react to>
open: <decisions still open and what unblocks each>
```

At handoff, return a single four-quadrant map plus the tweakable plan and
copyable implementation prompt. Do not replace the map with a plan, and do not
enter `handoff` before the first four stages are complete.

## Stopping condition

Stop at a stage boundary when user reaction or a blocking decision is needed.
Stop the walk with `OPEN` entries when evidence, ownership, or acceptance is
missing. A final map may contain visible uncertainty, but it is not complete
enough to hand off until the first four stages have been walked; a hidden
assumption or skipped stage is not acceptable.
