import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { loadManifest } from "../src/manifest.mjs";
import { installPrivateOverlay, resolvePrivateOverlay } from "../src/overlay.mjs";

const ROOT = process.cwd();
const CATALOG = path.join(ROOT, "catalog", "manifest.json");

function overlay(overrides = {}) {
  return {
    schema_version: "jas-private-overlay/v1",
    visibility: "private-overlay",
    overlay_id: "personal-overlay-fixture",
    base_workbench_id: "portable-agentic-workbench",
    references: [
      {
        id: "codex-context-budget",
        asset_id: "context-budget-governor",
        enabled: true,
        targets: ["codex", "generic"],
        destination: "$HOME/.codex/workbench/context-budget-governor"
      },
      {
        id: "claude-adapter-preview",
        asset_id: "adapter-claude",
        enabled: false,
        targets: ["claude"]
      }
    ],
    ...overrides
  };
}

function privateOverlay(overrides = {}) {
  return {
    schema_version: "jas-private-overlay/v2",
    visibility: "private-overlay",
    overlay_id: "private-workflow-overlay",
    base_workbench_id: "portable-agentic-workbench",
    references: [
      {
        id: "private-workflow-selection",
        asset_id: "private-workflow",
        enabled: true,
        targets: ["codex"],
        destination: "$HOME/.codex/workbench/private-workflow"
      }
    ],
    private_assets: [
      {
        id: "private-workflow",
        kind: "workflow",
        title: "Private workflow port",
        summary: "A sanitized private workflow package for one personal setup.",
        maturity: "experimental",
        supported_targets: ["codex"],
        package_ref: "artifact:private-package:private-workflow",
        package_dir: "private-workflow",
        entrypoints: ["SKILL.md"],
        files: ["SKILL.md", "WORKFLOW.md"],
        install: {
          mode: "copy",
          destination: "$HOME/.codex/workbench/private-workflow"
        }
      }
    ],
    ...overrides
  };
}

function publicMultiRootOverlay(overrides = {}) {
  return {
    schema_version: "jas-private-overlay/v1",
    visibility: "private-overlay",
    overlay_id: "public-multi-root-overlay",
    base_workbench_id: "portable-agentic-workbench",
    references: [
      {
        id: "skill-harvest-selection",
        asset_id: "skill-harvest-and-promotion",
        enabled: true,
        targets: ["codex"],
        destination: "$HOME/.codex/workbench/skill-harvest-and-promotion"
      }
    ],
    ...overrides
  };
}

function withOverlay(value, callback) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "jas-overlay-test-"));
  const overlayPath = path.join(root, "overlay.json");
  fs.writeFileSync(overlayPath, JSON.stringify(value), "utf8");
  try {
    return callback(overlayPath);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
}

test("publishes the private overlay contract without embedding a personal mapping", () => {
  const schema = JSON.parse(fs.readFileSync(path.join(ROOT, "schemas", "jas-private-overlay.schema.json"), "utf8"));
  assert.equal(schema.$id.endsWith("jas-private-overlay.schema.json"), true);
  assert.deepEqual(schema.required, ["schema_version", "visibility", "overlay_id", "base_workbench_id", "references"]);
  assert.deepEqual(schema.$defs.target.enum, ["generic", "codex", "claude", "gemini", "cursor", "antigravity", "copilot"]);
});

test("resolves a private overlay against eligible public assets without mutation", () => {
  const { manifest, manifestRoot } = loadManifest(path.join(ROOT, "manifest.yaml"));
  const result = withOverlay(overlay(), (overlayPath) => resolvePrivateOverlay({
    overlayPath,
    catalogPath: CATALOG,
    baseManifest: manifest,
    manifestRoot
  }));

  assert.equal(result.status, "OVERLAY_VALID");
  assert.equal(result.visibility, "private-overlay");
  assert.equal(result.mutated, false);
  assert.deepEqual(result.assets.map((asset) => asset.id), ["context-budget-governor"]);
  assert.equal(result.references.find((reference) => reference.id === "codex-context-budget").destination, "$HOME/.codex/workbench/context-budget-governor");
  assert.equal(result.catalog, "public-catalog");
});

test("resolves a private-only package without exposing its host path", () => {
  const { manifest, manifestRoot } = loadManifest(path.join(ROOT, "manifest.yaml"));
  const result = withOverlay(privateOverlay(), (overlayPath) => resolvePrivateOverlay({
    overlayPath,
    catalogPath: CATALOG,
    baseManifest: manifest,
    manifestRoot
  }));

  assert.equal(result.schema_version, "jas-private-overlay/v2");
  assert.equal(result.mutated, false);
  assert.equal(result.assets[0].source_kind, "private-package");
  assert.equal(result.assets[0].package_ref, "artifact:private-package:private-workflow");
  assert.equal("/Users/".includes(result.assets[0].package_dir), false);
});

test("CLI resolves the personal mode while leaving the public base report-only", () => {
  const result = withOverlay(overlay(), (overlayPath) => spawnSync(
    process.execPath,
    [path.join(ROOT, "bin", "agent-config.mjs"), "overlay", "--overlay", overlayPath, "--json"],
    { cwd: ROOT, encoding: "utf8" }
  ));
  assert.equal(result.status, 0);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.status, "OVERLAY_VALID");
  assert.equal(payload.mutated, false);
  assert.equal(result.stdout.includes("overlay.json"), false);
});

test("rejects private paths, unknown assets, and unsupported target mappings", () => {
  const { manifest, manifestRoot } = loadManifest(path.join(ROOT, "manifest.yaml"));
  const resolve = (value) => withOverlay(value, (overlayPath) => resolvePrivateOverlay({
    overlayPath,
    catalogPath: CATALOG,
    baseManifest: manifest,
    manifestRoot
  }));

  assert.throws(() => resolve(overlay({
    references: [{ ...overlay().references[0], destination: path.join(os.homedir(), "private-file") }]
  })), /symbolic root|safe symbolic/);
  assert.throws(() => resolve(overlay({
    references: [{ ...overlay().references[0], asset_id: "missing-asset" }]
  })), /unknown public asset/);
  assert.throws(() => resolve(overlay({
    references: [{ ...overlay().references[0], asset_id: "adapter-claude", targets: ["codex"] }]
  })), /not supported/);
});

test("rejects non-installable catalog assets and refuses apply mode", () => {
  const { manifest, manifestRoot } = loadManifest(path.join(ROOT, "manifest.yaml"));
  assert.throws(() => withOverlay(overlay({
    references: [{ ...overlay().references[0], asset_id: "reference-aios" }]
  }), (overlayPath) => resolvePrivateOverlay({
    overlayPath,
    catalogPath: CATALOG,
    baseManifest: manifest,
    manifestRoot
  })), /not eligible/);

  const result = withOverlay(overlay(), (overlayPath) => spawnSync(
    process.execPath,
    [path.join(ROOT, "bin", "agent-config.mjs"), "overlay", "--overlay", overlayPath, "--apply"],
    { cwd: ROOT, encoding: "utf8" }
  ));
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /report-only/);
});

test("plans, applies, and refuses to overwrite a private package install", () => {
  const { manifest, manifestRoot } = loadManifest(path.join(ROOT, "manifest.yaml"));
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "jas-private-install-test-"));
  const overlayPath = path.join(temporary, "overlay.json");
  const privateRoot = path.join(temporary, "private-packages");
  const packageRoot = path.join(privateRoot, "private-workflow");
  const targetRoot = path.join(temporary, "target");
  fs.mkdirSync(packageRoot, { recursive: true });
  fs.writeFileSync(path.join(packageRoot, "SKILL.md"), "private skill\n", "utf8");
  fs.writeFileSync(path.join(packageRoot, "WORKFLOW.md"), "private workflow\n", "utf8");
  fs.writeFileSync(overlayPath, JSON.stringify(privateOverlay()), "utf8");
  const cli = (extra = []) => spawnSync(
    process.execPath,
    [path.join(ROOT, "bin", "agent-config.mjs"), "overlay-install", "--overlay", overlayPath, "--private-root", privateRoot, "--root", targetRoot, "--json", ...extra],
    { cwd: ROOT, encoding: "utf8" }
  );

  try {
    const dryRun = cli();
    assert.equal(dryRun.status, 0);
    const planned = JSON.parse(dryRun.stdout);
    assert.equal(planned.status, "OVERLAY_INSTALL_READY");
    assert.equal(planned.mutated, false);
    assert.equal(planned.actions[0].source.startsWith("$PRIVATE_ROOT/private-workflow/"), true);
    assert.equal(fs.existsSync(targetRoot), false);

    const applied = cli(["--apply"]);
    assert.equal(applied.status, 0);
    const appliedPayload = JSON.parse(applied.stdout);
    assert.equal(appliedPayload.status, "OVERLAY_INSTALL_APPLIED");
    assert.equal(appliedPayload.mutated, true);
    assert.equal(fs.readFileSync(path.join(targetRoot, ".codex", "workbench", "private-workflow", "SKILL.md"), "utf8"), "private skill\n");
    assert.equal(fs.readFileSync(path.join(targetRoot, ".codex", "workbench", "private-workflow", "WORKFLOW.md"), "utf8"), "private workflow\n");

    const overwrite = cli(["--apply"]);
    assert.equal(overwrite.status, 2);
    const blocked = JSON.parse(overwrite.stdout);
    assert.equal(blocked.status, "OVERLAY_INSTALL_BLOCKED");
    assert.equal(blocked.mutated, false);
    assert.match(overwrite.stdout, /exists/);
    assert.equal(fs.readFileSync(path.join(targetRoot, ".codex", "workbench", "private-workflow", "SKILL.md"), "utf8"), "private skill\n");
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});

test("installs a public catalog asset whose files span multiple source roots", () => {
  const { manifest, manifestRoot } = loadManifest(path.join(ROOT, "manifest.yaml"));
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "jas-public-install-test-"));
  const overlayPath = path.join(temporary, "overlay.json");
  const targetRoot = path.join(temporary, "target");
  const catalogBefore = fs.readFileSync(CATALOG, "utf8");
  fs.writeFileSync(overlayPath, JSON.stringify(publicMultiRootOverlay()), "utf8");

  try {
    const dryRun = spawnSync(
      process.execPath,
      [path.join(ROOT, "bin", "agent-config.mjs"), "overlay-install", "--overlay", overlayPath, "--root", targetRoot, "--json"],
      { cwd: ROOT, encoding: "utf8" }
    );
    assert.equal(dryRun.status, 0);
    const planned = JSON.parse(dryRun.stdout);
    assert.equal(planned.status, "OVERLAY_INSTALL_READY");
    assert.deepEqual(planned.actions.map((action) => path.basename(action.destination)).sort(), ["SKILL.md", "WORKFLOW.md"]);
    assert.equal(planned.mutated, false);
    assert.equal(fs.existsSync(targetRoot), false);

    const applied = spawnSync(
      process.execPath,
      [path.join(ROOT, "bin", "agent-config.mjs"), "overlay-install", "--overlay", overlayPath, "--root", targetRoot, "--apply", "--json"],
      { cwd: ROOT, encoding: "utf8" }
    );
    assert.equal(applied.status, 0);
    const payload = JSON.parse(applied.stdout);
    assert.equal(payload.status, "OVERLAY_INSTALL_APPLIED");
    assert.equal(payload.mutated, true);
    assert.equal(fs.readFileSync(path.join(targetRoot, ".codex", "workbench", "skill-harvest-and-promotion", "SKILL.md"), "utf8"), fs.readFileSync(path.join(ROOT, "skills", "skill-harvest-and-promotion", "SKILL.md"), "utf8"));
    assert.equal(fs.readFileSync(path.join(targetRoot, ".codex", "workbench", "skill-harvest-and-promotion", "WORKFLOW.md"), "utf8"), fs.readFileSync(path.join(ROOT, "workflows", "skill-harvest-and-promotion", "WORKFLOW.md"), "utf8"));
    assert.equal(fs.readFileSync(CATALOG, "utf8"), catalogBefore);
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});

test("refuses a target root that resolves to the home directory", () => {
  const { manifest, manifestRoot } = loadManifest(path.join(ROOT, "manifest.yaml"));
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "jas-home-alias-test-"));
  const alias = path.join(temporary, "home-alias");
  fs.symlinkSync(os.homedir(), alias, "dir");

  try {
    withOverlay(privateOverlay(), (overlayPath) => assert.throws(() => installPrivateOverlay({
      overlayPath,
      catalogPath: CATALOG,
      baseManifest: manifest,
      manifestRoot,
      privateRoot: path.join(temporary, "private-packages"),
      targetRoot: alias
    }), /home directory/));
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});

test("blocks a broken destination symlink before applying a private package", () => {
  const { manifest, manifestRoot } = loadManifest(path.join(ROOT, "manifest.yaml"));
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "jas-broken-target-test-"));
  const overlayPath = path.join(temporary, "overlay.json");
  const privateRoot = path.join(temporary, "private-packages");
  const packageRoot = path.join(privateRoot, "private-workflow");
  const targetRoot = path.join(temporary, "target");
  const destinationRoot = path.join(targetRoot, ".codex", "workbench", "private-workflow");
  fs.mkdirSync(packageRoot, { recursive: true });
  fs.writeFileSync(path.join(packageRoot, "SKILL.md"), "private skill\n", "utf8");
  fs.writeFileSync(path.join(packageRoot, "WORKFLOW.md"), "private workflow\n", "utf8");
  fs.mkdirSync(destinationRoot, { recursive: true });
  fs.symlinkSync(path.join(temporary, "missing-target"), path.join(destinationRoot, "SKILL.md"));
  fs.writeFileSync(overlayPath, JSON.stringify(privateOverlay()), "utf8");

  try {
    const result = spawnSync(
      process.execPath,
      [path.join(ROOT, "bin", "agent-config.mjs"), "overlay-install", "--overlay", overlayPath, "--private-root", privateRoot, "--root", targetRoot, "--apply", "--json"],
      { cwd: ROOT, encoding: "utf8" }
    );
    assert.equal(result.status, 2);
    const payload = JSON.parse(result.stdout);
    assert.equal(payload.status, "OVERLAY_INSTALL_BLOCKED");
    assert.equal(payload.mutated, false);
    assert.equal(payload.actions.find((action) => action.destination.endsWith("SKILL.md")).status, "exists");
    assert.equal(fs.lstatSync(path.join(destinationRoot, "SKILL.md")).isSymbolicLink(), true);
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});

test("rejects private package traversal before installation", () => {
  const { manifest, manifestRoot } = loadManifest(path.join(ROOT, "manifest.yaml"));
  assert.throws(() => withOverlay(privateOverlay({
    private_assets: [{ ...privateOverlay().private_assets[0], package_dir: "../escape" }]
  }), (overlayPath) => resolvePrivateOverlay({
    overlayPath,
    catalogPath: CATALOG,
    baseManifest: manifest,
    manifestRoot
  })), /safe relative path/);
});
