#!/usr/bin/env node

import path from "node:path";
import {
  bootstrapRuntimes,
  collectAudit,
  collectDrift,
  defaultManifestPath,
  doctorManifest,
  formatEntryTable,
  loadManifest,
  smokeRuntimes,
  syncManifest,
  writeAuditReports
} from "../src/agent-config.mjs";
import { installPrivateOverlay, resolvePrivateOverlay } from "../src/overlay.mjs";

function parseArgs(argv) {
  const args = { command: argv[0] ?? "help", json: false, apply: false, allowBroadScan: false, allowHome: false, provider: null };
  if (args.command === "--help" || args.command === "-h") args.command = "help";
  for (let index = 1; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--json") args.json = true;
    else if (value === "--apply") args.apply = true;
    else if (value === "--dry-run") args.apply = false;
    else if (value === "--allow-broad-scan") args.allowBroadScan = true;
    else if (value === "--allow-home") args.allowHome = true;
    else if (value === "--manifest") {
      args.manifest = argv[++index];
      if (!args.manifest) throw new Error("--manifest requires a path");
    } else if (value === "--overlay") {
      args.overlay = argv[++index];
      if (!args.overlay) throw new Error("--overlay requires a path");
    } else if (value === "--catalog") {
      args.catalog = argv[++index];
      if (!args.catalog) throw new Error("--catalog requires a path");
    } else if (value === "--private-root") {
      args.privateRoot = argv[++index];
      if (!args.privateRoot) throw new Error("--private-root requires a path");
    } else if (value === "--root") {
      args.root = argv[++index];
      if (!args.root) throw new Error("--root requires a path");
    } else if (value === "--provider") {
      args.provider = argv[++index];
      if (!args.provider) throw new Error("--provider requires a target");
    } else if (value === "--help" || value === "-h") args.command = "help";
    else throw new Error(`unknown option ${value}`);
  }
  return args;
}

function print(value, json) {
  process.stdout.write(`${json ? JSON.stringify(value, null, 2) : value}\n`);
}

function help() {
  return `Usage: agent-config <audit|drift|doctor|sync|install|bootstrap|smoke|overlay|overlay-install> [options]

Commands are read-only by default.
  audit   inventory surfaces, lint always-loaded files, and write audit reports
  drift   compare manifest entries against the last safe baseline
  doctor  validate targets, conflicts, links, and runtime availability
  sync    preview safe sync actions; use --apply to write missing targets
  install preview the same safe manifest install path; use --apply to write
  bootstrap report known CLI recipes and verify available commands
  smoke   run non-destructive --help checks for available runtimes
  overlay resolve a private companion overlay against the public catalog
  overlay-install plan or apply an overlay into an explicit disposable root

Options:
  --manifest <path>       manifest path (default: repository manifest.yaml)
  --overlay <path>        private companion overlay for the overlay command
  --catalog <path>        public catalog path (default: catalog/manifest.json)
  --private-root <path>   private package root for jas-private-overlay/v2
  --root <path>           repository root for sync plans or disposable target root for overlay-install
  --provider <target>     target adapter for sync (for example codex)
  --allow-broad-scan      permit an explicitly requested home inventory scan
  --allow-home            permit the explicit Pronto promotion path to target the real home
  --apply                 allow safe writes after the full preflight passes
  --dry-run               force report-only behavior (the default)
  --json                  emit machine-readable output

Audit alternative: agent-config sync --provider codex --root <repo> --dry-run --json
This is a plan only: no provider projection or live target mutation occurs.
When selecting a command without executing it, describe it as a proposed plan;
do not report output, projection, or mutation that was not observed. Unsupported
tokens are rejected and routed to help; do not infer exact stderr, exit codes, or
JSON error formatting from this interface.
When an overlay install is blocked, use this audit/dry-run alternative; do not
infer home-install authority from the request.
`;
}

function main(argv) {
  const args = parseArgs(argv);
  if (args.command === "help") {
    print(help(), false);
    return 0;
  }
  const manifestPath = args.manifest ?? (
    args.root && args.command !== "overlay-install"
      ? path.join(args.root, "manifest.yaml")
      : defaultManifestPath()
  );
  const { manifest, manifestRoot } = loadManifest(manifestPath);
  if (args.command === "overlay") {
    if (!args.overlay) throw new Error("overlay requires --overlay <path>");
    if (args.apply) throw new Error("overlay is report-only; remove --apply");
    const result = resolvePrivateOverlay({
      overlayPath: args.overlay,
      catalogPath: args.catalog ?? path.join(manifestRoot, "catalog", "manifest.json"),
      baseManifest: manifest,
      manifestRoot
    });
    print(args.json ? result : `${result.status}\noverlay: ${result.overlay_id}\nassets: ${result.assets.map((asset) => asset.id).join(", ") || "none"}\nmutated: ${result.mutated}`, args.json);
    return 0;
  }
  if (args.command === "overlay-install") {
    if (!args.overlay) throw new Error("overlay-install requires --overlay <path>");
    if (!args.root) throw new Error("overlay-install requires --root <path>");
    if (args.allowHome && path.resolve(args.root) !== path.resolve(process.env.HOME ?? "")) {
      throw new Error("--allow-home requires --root to be the real home directory");
    }
    const result = installPrivateOverlay({
      overlayPath: args.overlay,
      catalogPath: args.catalog ?? path.join(manifestRoot, "catalog", "manifest.json"),
      baseManifest: manifest,
      manifestRoot,
      privateRoot: args.privateRoot,
      targetRoot: args.root,
      apply: args.apply,
      allowHome: args.allowHome
    });
    print(args.json ? result : `${result.status}${args.apply ? " (applied)" : " (dry run)"}\nroot: ${result.root}\nactions: ${result.actions.length}\nmutated: ${result.mutated}`, args.json);
    return result.status === "OVERLAY_INSTALL_BLOCKED" ? 2 : 0;
  }
  if (args.command === "audit") {
    const result = collectAudit(manifest, manifestRoot, { allowBroadScan: args.allowBroadScan });
    writeAuditReports(result, manifestRoot);
    print(args.json ? result : `status: ${result.status}\nentries: ${result.entries.length}\nconflicts: ${result.conflicts.length}\nduplicates: ${result.duplicates.length}\naudit: ${manifestRoot}/audit`, args.json);
    return 0;
  }
  if (args.command === "drift") {
    const result = collectDrift(manifest, manifestRoot);
    print(args.json ? result : `${result.status}\n${formatEntryTable(result.entries)}\nunknown_live: ${result.unknown_live.length}`, args.json);
    return result.status === "DRIFT_PRESENT" ? 2 : 0;
  }
  if (args.command === "doctor") {
    const result = doctorManifest(manifest, manifestRoot);
    print(args.json ? result : `${result.status}\n${result.findings.map((item) => `${item.severity}: ${item.id}: ${item.message}`).join("\n") || "no findings"}`, args.json);
    return result.status === "DOCTOR_BLOCKED" ? 2 : 0;
  }
  if (args.command === "sync" || args.command === "install") {
    if (args.provider && !["generic", "codex", "claude", "cursor", "copilot", "gemini", "antigravity"].includes(args.provider)) {
      throw new Error(`unsupported provider ${args.provider}; run agent-config help`);
    }
    const result = syncManifest(manifest, manifestRoot, { apply: args.apply });
    print(args.json ? result : `${result.status}${args.apply ? " (applied safe actions)" : " (dry run)"}\n${result.actions.map((item) => `${item.action}: ${item.id}: ${item.reason}`).join("\n")}`, args.json);
    return result.status === "SYNC_BLOCKED" ? 2 : 0;
  }
  if (args.command === "smoke") {
    const result = smokeRuntimes(manifest);
    print(args.json ? result : `${result.status}\n${result.results.map((item) => `${item.status}: ${item.runtime} (${item.command})`).join("\n")}`, args.json);
    return result.status === "SMOKE_FAILED" ? 2 : 0;
  }
  if (args.command === "bootstrap") {
    const config = syncManifest(manifest, manifestRoot, { apply: args.apply });
    const runtimes = bootstrapRuntimes(manifest);
    const result = { generated_at: new Date().toISOString(), apply: args.apply, config, runtimes };
    print(args.json ? result : `${runtimes.status}\n${runtimes.results.map((item) => `${item.status}: ${item.runtime} — ${item.install_recipe}`).join("\n")}\nconfig: ${config.status}`, args.json);
    return config.status === "SYNC_BLOCKED" || runtimes.status === "BOOTSTRAP_NEEDS_MANUAL_INSTALL" ? 2 : 0;
  }
  throw new Error(`unknown command ${args.command}; run agent-config help`);
}

try {
  process.exitCode = main(process.argv.slice(2));
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
}
