# Case study: safe tool guards

## Problem

Agentic workflows can make a read-only request look like a write, resolve a
target too broadly, or silently register a hook while installing an otherwise
portable asset. A successful process exit does not prove that the intended
scope was preserved.

## Mechanism

`safe-tool-guards` classifies actions, resolves targets, previews mutations,
requires explicit approval where appropriate, rejects unresolved or unsafe
scope, and verifies the result. Host adapters are staged and reviewed rather
than registered by the installer.

## Evidence

The audit observed a shared guard behavior across multiple agent surfaces. The
workbench expresses that behavior as a small contract and the installer tests
no-overwrite, explicit-root, dry-run, and missing-dependency behavior in a
disposable directory.

## Limitation

The contract is not a sandbox and does not replace a host's operating-system
permissions. It does not claim that every vendor exposes the same hook or
approval surface.
