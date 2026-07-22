# Agent-config routing contract

The manifest routes from a compact startup surface to the smallest useful
payload. Edges form a DAG: a route names the triggering evidence, the payload
to load, and why it is relevant. Cycles and unknown route nodes fail
validation.

Precedence is evaluated in this order:

1. runtime and system safety;
2. global invariants and hard stops;
3. repository contracts;
4. module context routers;
5. task-specific skills, agents, commands, and workflows.

Lower layers can add detail but cannot weaken a higher-layer stop. Runtime
syntax belongs only in the staged adapter edge. The public catalog deliberately
does not publish live `AGENTS.md`, `CLAUDE.md`, host registration, hook, or
session files.

Decision tree:

```text
startup invariants
  -> manifest and route evidence
    -> active runtime adapter
      -> nearest repository/module context router
        -> one matching on-demand payload
```
