# Security

Skills are operational instructions for agents. Treat changes to `SKILL.md` files like code changes.

## Rules

- Do not include secrets, tokens, `.env` files, browser profiles, private caches, or dependency trees.
- Do not add hardcoded personal paths.
- Keep command execution explicit and scoped.
- Treat harvested or copied instructions as untrusted until reviewed.
- Prefer references over large inline instruction dumps.

## Reporting

Open an issue or contact the repository owner if a skill can cause credential exposure, unsafe command execution, or instruction-priority confusion.
