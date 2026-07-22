import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import {
  bootstrapRuntimes,
  collectAudit,
  compareSnapshots,
  detectRouteCycle,
  doctorManifest,
  expandPath,
  lintAlwaysLoaded,
  parseManifestText,
  snapshotPath,
  syncManifest,
  validateManifest
} from "../src/agent-config.mjs";

function minimalManifest(overrides = {}) {
  return {
    schema_version: 1,
    manifest_id: "test",
    roots: { test: "$MANIFEST_ROOT" },
    entries: [{
      id: "entry",
      source: "source.md",
      destination: "$HOME/destination.md",
      owner: "canonical",
      runtime: ["codex"],
      layer: "runtime-adapter",
      always_loaded: true,
      path_kind: "file",
      sync_direction: "push-only",
      provenance: "test",
      install_recipe: "test",
      status: "active"
    }],
    inventory_scopes: [{ id: "scope", root: "$MANIFEST_ROOT", max_depth: 2, patterns: ["*.md"], excludes: [] }],
    routes: [],
    ...overrides
  };
}

test("parses JSON-compatible YAML and validates the manifest contract", () => {
  const manifest = minimalManifest();
  assert.deepEqual(parseManifestText(JSON.stringify(manifest)), manifest);
  assert.equal(validateManifest(manifest), true);
});

test("publishes a schema with the required fields and all supported runtime adapters", () => {
  const schema = JSON.parse(fs.readFileSync(path.join(process.cwd(), "schemas", "agent-config-manifest.schema.json"), "utf8"));
  assert.deepEqual(schema.$defs.entry.required, [
    "id", "source", "destination", "owner", "runtime", "layer", "always_loaded",
    "path_kind", "sync_direction", "provenance", "install_recipe", "status"
  ]);
  assert.deepEqual(schema.$defs.runtime.enum, ["claude", "codex", "gemini", "cursor", "antigravity"]);
});

test("rejects host-specific absolute paths and credential-shaped values", () => {
  assert.throws(() => validateManifest(minimalManifest({ entries: [{ ...minimalManifest().entries[0], source: path.join(os.homedir(), "secret.md") }] })), /absolute path/);
  assert.throws(() => validateManifest(minimalManifest({ entries: [{ ...minimalManifest().entries[0], source: "~" + "/secret.md" }] })), /home shorthand/);
  assert.throws(() => validateManifest(minimalManifest({ entries: [{ ...minimalManifest().entries[0], source: "../secret.md" }] })), /unsafe path segment/);
  assert.throws(() => validateManifest(minimalManifest({ entries: [{ ...minimalManifest().entries[0], runtime: ["unsupported"] }] })), /unsupported runtime/);
  assert.throws(() => validateManifest(minimalManifest({ description: `token=${"x".repeat(16)}` })), /credential|secret/);
});

test("expands portable manifest roots without requiring a host path", () => {
  const manifestRoot = "/tmp/agent-config-test";
  const manifest = minimalManifest();
  assert.equal(expandPath("$MANIFEST_ROOT/source.md", manifest, manifestRoot), path.join(manifestRoot, "source.md"));
  assert.equal(expandPath("$HOME/.agents", manifest, manifestRoot), path.join(os.homedir(), ".agents"));
});

test("detects route cycles and accepts a decision-tree DAG", () => {
  assert.deepEqual(detectRouteCycle([{ from: "a", to: "b" }, { from: "b", to: "c" }]), []);
  assert.deepEqual(detectRouteCycle([{ from: "a", to: "b" }, { from: "b", to: "a" }]), ["a", "b", "a"]);
  assert.throws(() => validateManifest(minimalManifest({ routes: [{ id: "broken", from: "entry", to: "missing", when: "never", load: "on-demand", reason: "test" }] })), /unknown entry/);
});

test("structural always-loaded lint reports procedure content without using a line budget", () => {
  const safe = lintAlwaysLoaded("# Router\n\nRead the matching playbook route on demand.\n");
  assert.equal(safe.line_count, 4);
  assert.deepEqual(safe.findings, []);
  const detailed = lintAlwaysLoaded("# Router\n\n1. Run pnpm test.\n```sh\nnode script.mjs\n```\n");
  assert.ok(detailed.findings.some((finding) => finding.code === "embedded-command-procedure"));
  assert.ok(detailed.findings.some((finding) => finding.code === "embedded-procedure"));
});

test("comparison states cover equal, one-sided, and baseline-backed modifications", () => {
  const a = { kind: "file", hash: "a" };
  const b = { kind: "file", hash: "b" };
  const c = { kind: "file", hash: "c" };
  assert.equal(compareSnapshots(a, a), "equal");
  assert.equal(compareSnapshots(a, null), "repo-only");
  assert.equal(compareSnapshots(null, a), "live-only");
  assert.equal(compareSnapshots(b, a, a), "repo-modified");
  assert.equal(compareSnapshots(a, b, a), "live-modified");
  assert.equal(compareSnapshots(b, c, a), "both-modified");
  assert.equal(compareSnapshots(b, c), "diverged-no-baseline");
});

test("directory snapshots include relative members and hashes", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-config-test-"));
  try {
    fs.mkdirSync(path.join(root, "nested"));
    fs.writeFileSync(path.join(root, "a.md"), "a\n");
    fs.writeFileSync(path.join(root, "nested", "b.md"), "b\n");
    const snapshot = snapshotPath(root);
    assert.equal(snapshot.kind, "directory");
    assert.deepEqual(snapshot.files.map((file) => file.path), ["a.md", "nested/b.md"]);
    assert.match(snapshot.hash, /^[a-f0-9]{64}$/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("symlink snapshots preserve link provenance", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-config-link-"));
  try {
    const target = path.join(root, "target.md");
    const link = path.join(root, "link.md");
    fs.writeFileSync(target, "target\n");
    fs.symlinkSync("target.md", link);
    const snapshot = snapshotPath(link);
    assert.equal(snapshot.kind, "symlink");
    assert.equal(snapshot.target, "target.md");
    assert.equal(snapshot.broken, false);
    assert.match(snapshot.hash, /^[a-f0-9]{64}$/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("safe sync applies a source-only file, records a baseline, and blocks live edits", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-config-sync-"));
  try {
    const manifest = minimalManifest({
      entries: [{ ...minimalManifest().entries[0], source: "source.md", destination: "destination.md", always_loaded: false, runtime: [] }],
      runtime_commands: []
    });
    fs.writeFileSync(path.join(root, "source.md"), "canonical\n");
    const dryRun = syncManifest(manifest, root, { apply: false });
    assert.equal(dryRun.actions[0].action, "copy-source-to-destination");
    assert.equal(fs.existsSync(path.join(root, "destination.md")), false);
    const applied = syncManifest(manifest, root, { apply: true });
    assert.equal(applied.status, "SYNC_CLEAN");
    assert.equal(fs.readFileSync(path.join(root, "destination.md"), "utf8"), "canonical\n");
    fs.writeFileSync(path.join(root, "destination.md"), "live edit\n");
    const blocked = syncManifest(manifest, root, { apply: false });
    assert.equal(blocked.actions[0].action, "blocked");
    assert.equal(blocked.actions[0].reason, "live-modified");
    const noOverwrite = syncManifest(manifest, root, { apply: true });
    assert.equal(noOverwrite.status, "SYNC_BLOCKED");
    assert.equal(fs.readFileSync(path.join(root, "destination.md"), "utf8"), "live edit\n");
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("safe sync preflights every action and never partially applies around a conflict", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-config-preflight-"));
  try {
    const base = minimalManifest().entries[0];
    const manifest = minimalManifest({
      entries: [
        { ...base, id: "conflict", source: "canonical.md", destination: "live.md", runtime: [], always_loaded: false },
        { ...base, id: "new-entry", source: "new.md", destination: "new-live.md", runtime: [], always_loaded: false }
      ],
      runtime_commands: []
    });
    fs.writeFileSync(path.join(root, "canonical.md"), "original\n");
    fs.writeFileSync(path.join(root, "live.md"), "original\n");
    fs.mkdirSync(path.join(root, ".agent-config-state"));
    fs.writeFileSync(path.join(root, ".agent-config-state", "baselines.json"), JSON.stringify({
      conflict: { hash: snapshotPath(path.join(root, "canonical.md")).hash, kind: "file" }
    }));
    fs.writeFileSync(path.join(root, "canonical.md"), "repo edit\n");
    fs.writeFileSync(path.join(root, "new.md"), "new canonical\n");

    const result = syncManifest(manifest, root, { apply: true });
    assert.equal(result.status, "SYNC_BLOCKED");
    assert.ok(result.blocked >= 1);
    assert.equal(fs.existsSync(path.join(root, "new-live.md")), false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("audit and doctor expose missing targets and broken symlinks", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-config-links-"));
  try {
    const base = minimalManifest().entries[0];
    const manifest = minimalManifest({
      entries: [
        { ...base, id: "missing", source: "missing.md", destination: "missing-live.md", runtime: [], always_loaded: false },
        { ...base, id: "broken", source: "broken.md", destination: "broken-live.md", runtime: [], always_loaded: false, path_kind: "symlink" }
      ],
      runtime_commands: []
    });
    fs.symlinkSync("absent.md", path.join(root, "broken.md"));
    validateManifest(manifest);
    const audit = collectAudit(manifest, root, { allowBroadScan: false });
    assert.ok(audit.conflicts.some((item) => item.type === "missing-target"));
    assert.ok(audit.conflicts.some((item) => item.type === "broken-link"));
    const doctor = doctorManifest(manifest, root);
    assert.equal(doctor.status, "DOCTOR_BLOCKED");
    assert.ok(doctor.findings.some((item) => item.message.includes("symlink")));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("safe sync blocks unknown live directory members", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "agent-config-live-member-"));
  try {
    const manifest = minimalManifest({
      entries: [{ ...minimalManifest().entries[0], id: "directory", source: "source-dir", destination: "destination-dir", always_loaded: false, path_kind: "directory", sync_direction: "bidirectional", runtime: [] }],
      runtime_commands: []
    });
    fs.mkdirSync(path.join(root, "source-dir"));
    fs.mkdirSync(path.join(root, "destination-dir"));
    fs.writeFileSync(path.join(root, "source-dir", "known.md"), "known\n");
    fs.writeFileSync(path.join(root, "destination-dir", "known.md"), "known\n");
    fs.writeFileSync(path.join(root, "destination-dir", "live-only.md"), "preserve\n");
    const result = syncManifest(manifest, root, { apply: false });
    assert.equal(result.status, "SYNC_BLOCKED");
    assert.equal(result.actions[0].reason, "unknown live members require review");
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("bootstrap reports installed, manual, and GUI-dependent runtimes without installing", () => {
  const result = bootstrapRuntimes({ runtime_commands: [
    { runtime: "codex", command: "node", verification: "node --help", install_recipe: "package-manager" },
    { runtime: "cursor", command: "missing-runtime-for-test", verification: "missing-runtime-for-test --help", install_recipe: "GUI-dependent; report only" }
  ] });
  assert.equal(result.status, "BOOTSTRAP_PARTIAL");
  assert.equal(result.results[0].status, "installed");
  assert.equal(result.results[1].status, "unverified");
});
