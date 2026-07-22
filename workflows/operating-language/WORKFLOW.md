# Operating Language

Use this workflow to turn repeated reasoning into a small, shared vocabulary that improves routing without becoming a new layer of vague process.

## 1. Extract terms by layer

Collect repeated terms from domain behavior, architecture, observed interaction, product strategy, and user need. Preserve the layer where each term is useful. A term that only names a tool or a personal preference is not automatically operating language.

## 2. Apply the Leading Word Test

For each candidate term, ask whether it changes what an agent should inspect, decide, execute, verify, or refuse. If the answer is no, keep it as ordinary prose or remove it. Prefer a term that names a behavior and its boundary over a slogan.

## 3. Publish a compact contract

Use a table with `term`, `layer`, `trigger`, `non_trigger`, `decision`, `completion_evidence`, `owner`, and `status`. Include one example and one counterexample. Link the term to the skill or workflow that implements it.

## 4. Migrate carefully

Introduce the term in the narrowest routing surface, measure whether it improves decisions, and record conflicts or drift. Do not rewrite every instruction at once. Retire a term when it no longer changes behavior or when a clearer canonical term replaces it.

See [the skill contract](../../skills/operating-language/SKILL.md).
