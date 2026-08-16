import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { validateAgentUsability } from "../scripts/check_agent_usability.mjs";

function writeContract(root, contract) {
  fs.mkdirSync(path.join(root, ".agents"), { recursive: true });
  fs.writeFileSync(
    path.join(root, ".agents", "agent-usability.json"),
    JSON.stringify(contract)
  );
}

function writeEvidence(root, relativePath = "docs/behavior.json") {
  const target = path.join(root, relativePath);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, "{}\n");
}

function contract(applicability, behaviorEvidence) {
  return {
    schema: "agent-usability/v1",
    reviewed_at: "2026-07-25",
    applicability,
    ...(applicability === "not-applicable" ? { reason: "fixture has no supported agent tool surface" } : {}),
    tools: [{ id: "fixture-tool", behavior_evidence: behaviorEvidence }]
  };
}

test("the checked-in agent-usability contract has behavior evidence for every tool", () => {
  const result = validateAgentUsability(process.cwd());
  assert.equal(result.status, "pass");
  assert.deepEqual(result.errors, []);
  assert.equal(result.checks.tools_with_behavior_evidence, result.checks.declared_tools);
});

test("applicable contracts fail when a declared tool has no behavior evidence", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-usability-empty-"));
  try {
    writeContract(root, contract("applicable", []));
    const result = validateAgentUsability(root);
    assert.equal(result.status, "fail");
    assert.ok(result.errors.includes("agent-usability tool fixture-tool: no behavior evidence declared"));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("applicable contracts require evidence for every declared tool", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-usability-tools-"));
  try {
    writeEvidence(root);
    writeContract(root, {
      ...contract("applicable", [{ path: "docs/behavior.json" }]),
      tools: [
        { id: "covered-tool", behavior_evidence: [{ path: "docs/behavior.json" }] },
        { id: "uncovered-tool", behavior_evidence: [] }
      ]
    });
    const result = validateAgentUsability(root);
    assert.equal(result.status, "fail");
    assert.ok(result.errors.includes("agent-usability tool uncovered-tool: no behavior evidence declared"));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("not-applicable contracts may omit behavior evidence", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-usability-not-applicable-"));
  try {
    writeContract(root, contract("not-applicable", []));
    const result = validateAgentUsability(root);
    assert.equal(result.status, "pass");
    assert.deepEqual(result.errors, []);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("the validator is executable as a focused JSON quality check", () => {
  const output = execFileSync(
    process.execPath,
    [path.join(process.cwd(), "scripts", "check_agent_usability.mjs"), "--root", process.cwd()],
    { encoding: "utf8" }
  );
  const result = JSON.parse(output);
  assert.equal(result.status, "pass");
  assert.equal(result.schema_version, "agent-usability-check/v1");
});

test("applicable evidence must reference an existing repository file", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-usability-missing-"));
  try {
    writeEvidence(root, "docs/other.json");
    writeContract(root, contract("applicable", [{ path: "docs/missing.json" }]));
    const result = validateAgentUsability(root);
    assert.equal(result.status, "fail");
    assert.ok(result.errors.includes("agent-usability tool fixture-tool: missing behavior evidence docs/missing.json"));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
