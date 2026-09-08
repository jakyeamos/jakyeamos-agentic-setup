import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import {
  freshnessEvidence,
  summarizeDimensionStatuses,
  validateContract
} from "../scripts/check_environment_contract.mjs";

const PACKETS = [
  "architecture.md",
  "commands.md",
  "conventions.md",
  "security.md",
  "failure-modes.md",
  "examples.md",
  "done.md",
  "deployment.md"
];
const QUALITY_COMMANDS = [
  "pnpm lint",
  "pnpm typecheck",
  "pnpm test",
  "pnpm build",
  "pnpm check",
  "python3 scripts/pre_cr_coverage.py",
  "python3 skills/project-compass/scripts/project_compass.py gate . --json"
];

function writeFixture(root, indexSuffix = "", reviewedAt = "2026-07-25") {
  fs.mkdirSync(path.join(root, ".agents", "context"), { recursive: true });
  fs.mkdirSync(path.join(root, "catalog"), { recursive: true });
  fs.mkdirSync(path.join(root, "docs"), { recursive: true });
  fs.mkdirSync(path.join(root, "scripts"), { recursive: true });
  fs.writeFileSync(path.join(root, "AGENTS.md"), "# Router\n");
  fs.writeFileSync(path.join(root, "README.md"), "# Fixture\n");
  fs.writeFileSync(path.join(root, "SECURITY.md"), "# Security\n");
  fs.writeFileSync(path.join(root, "catalog", "manifest.json"), "{}\n");
  fs.writeFileSync(path.join(root, "scripts", "validate_repository.py"), "# validator\n");
  fs.writeFileSync(path.join(root, "scripts", "check_agent_usability.mjs"), "// checker\n");
  fs.writeFileSync(path.join(root, "scripts", "check_javascript.mjs"), "// checker\n");
  fs.writeFileSync(path.join(root, "docs", "fixture-behavior.json"), "{}\n");
  fs.writeFileSync(
    path.join(root, ".agents", "agent-usability.json"),
    JSON.stringify({
      schema: "agent-usability/v1",
      reviewed_at: "2026-07-25",
      applicability: "applicable",
      tools: [
        {
          id: "fixture-tool",
          behavior_evidence: [{ path: "docs/fixture-behavior.json" }]
        }
      ]
    })
  );
  fs.writeFileSync(path.join(root, ".gitignore"), ".env\n.env.*\nnode_modules/\n.pre-cr/\naudit/\n.aios/\n.quality-runner/\n");
  fs.writeFileSync(
    path.join(root, "package.json"),
    JSON.stringify({
      packageManager: "pnpm@11.9.0",
      scripts: {
        test: "node --test",
        lint: "python3 scripts/validate_repository.py",
        typecheck: "node scripts/check_javascript.mjs",
        build: "python3 scripts/validate_catalog.py",
        check: "node scripts/check_environment_contract.mjs"
      }
    })
  );
  fs.writeFileSync(
    path.join(root, ".pre-cr.json"),
    JSON.stringify({
      qualityCommands: QUALITY_COMMANDS,
      qualityAdapters: [{ name: "environment-contract", command: "node scripts/check_environment_contract.mjs", required: true }]
    })
  );
  const links = PACKETS.map((packet) => `[${packet}](${packet})`).join("\n");
  fs.writeFileSync(
    path.join(root, ".agents", "context", "README.md"),
    `# Context\n\nlast_reviewed: ${reviewedAt}\n\n${links}\n${indexSuffix}`
  );
  for (const packet of PACKETS) {
    fs.writeFileSync(path.join(root, ".agents", "context", packet), `# ${packet}\n`);
  }
}

test("the checked-in environment contract is currently valid", () => {
  const result = validateContract(process.cwd(), "2026-07-25", ["AGENTS.md"]);
  assert.equal(result.status, "pass");
  assert.deepEqual(result.errors, []);
  assert.equal(result.checks.context_packets, 8);
});

test("the contract rejects broken context links", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "environment-contract-links-"));
  try {
    writeFixture(root, "[broken](missing.md)\n");
    const result = validateContract(root, "2026-07-25", ["AGENTS.md"]);
    assert.equal(result.status, "fail");
    assert.ok(result.errors.includes("broken context link: missing.md"));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("freshness evidence reports the measured review age and limit", () => {
  assert.deepEqual(
    freshnessEvidence("2026-08-01", "2026-08-13"),
    { status: "pass", age_days: 12, limit_days: 35 }
  );
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "environment-contract-freshness-"));
  try {
    writeFixture(root, "", "2026-08-01");
    const result = validateContract(root, "2026-08-13", ["AGENTS.md"]);
    assert.equal(result.checks.context_dimensions.freshness, "pass");
    assert.deepEqual(result.checks.context_dimensions.freshness_evidence, {
      status: "pass",
      age_days: 12,
      limit_days: 35
    });
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("dimension-only reports retain freshness evidence", () => {
  const summary = summarizeDimensionStatuses({
    checks: {
      context_dimensions: {
        ownership: "pass",
        freshness: "pass",
        freshness_evidence: { status: "pass", age_days: 12, limit_days: 35 },
        links: "pass"
      },
      package_manager: { status: "pass" },
      quality_gates: { test: { status: "pass" } },
      ignore_rules: { ".env": { status: "pass" } },
      tracked_secret_custody: "pass"
    }
  });
  assert.deepEqual(summary, {
    ownership: "pass",
    freshness: { status: "pass", age_days: 12, limit_days: 35 },
    links: "pass",
    package_manager: "pass",
    quality_gates: { test: "pass" },
    ignore_rules: { ".env": "pass" },
    tracked_secret_custody: "pass"
  });
});

test("the contract rejects missing routed packets", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "environment-contract-packets-"));
  try {
    writeFixture(root);
    fs.rmSync(path.join(root, ".agents", "context", "security.md"));
    const result = validateContract(root, "2026-07-25", ["AGENTS.md"]);
    assert.equal(result.status, "fail");
    assert.ok(result.errors.includes("missing context packet: security.md"));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("the environment contract rejects applicable tools with no behavior evidence", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "environment-contract-usability-"));
  try {
    writeFixture(root);
    const usabilityPath = path.join(root, ".agents", "agent-usability.json");
    const usability = JSON.parse(fs.readFileSync(usabilityPath, "utf8"));
    usability.tools[0].behavior_evidence = [];
    fs.writeFileSync(usabilityPath, JSON.stringify(usability));

    const result = validateContract(root, "2026-07-25", ["AGENTS.md"]);
    assert.equal(result.status, "fail");
    assert.ok(result.errors.includes("agent-usability tool fixture-tool: no behavior evidence declared"));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
