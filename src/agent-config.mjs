import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { bootstrapRuntimes, runtimeAvailability, smokeRuntimes } from "./runtime.mjs";
import { defaultManifestPath, expandPath, loadManifest, parseManifestText, validateManifest } from "./manifest.mjs";
import { detectRouteCycle, lintAlwaysLoaded } from "./routing.mjs";
import { compareSnapshots, discoverScope, displayPath, entryPaths, entryReport, loadBaselines, saveBaselines, snapshotPath, statOrNull } from "./snapshots.mjs";
import { installPrivateOverlay, resolvePrivateOverlay } from "./overlay.mjs";

export { bootstrapRuntimes, compareSnapshots, defaultManifestPath, detectRouteCycle, discoverScope, expandPath, installPrivateOverlay, lintAlwaysLoaded, loadManifest, parseManifestText, resolvePrivateOverlay, smokeRuntimes, snapshotPath, validateManifest };

function canApply(entry, report, availability) {
  if (entry.sync_direction === "none" || entry.sync_direction === "report-only") return { action: "report-only", reason: "manifest is read-only" };
  if (report.source_broken || report.destination_broken) return { action: "blocked", reason: "broken symlink" };
  if (entry.status === "active" && !report.source_exists) return { action: "blocked", reason: "missing canonical source" };
  if (entry.status === "conflict") return { action: "blocked", reason: "conflict ledger entry" };
  if (entry.status === "excluded") return { action: "blocked", reason: "excluded class" };
  if (entry.status === "unverified") return { action: "blocked", reason: "entry is unverified" };
  if (entry.runtime.some((runtime) => availability[runtime] === null || availability[runtime] === undefined)) return { action: "blocked", reason: "runtime unavailable" };
  if (report.live_only.length > 0) return { action: "blocked", reason: "unknown live members require review" };
  if (report.state === "equal" || report.state === "missing-both") return { action: "none", reason: report.state };
  if (report.state === "repo-only") return { action: "copy-source-to-destination", reason: report.state };
  if (report.state === "live-only" && entry.sync_direction === "bidirectional") return { action: "copy-destination-to-source", reason: report.state };
  if (report.state === "repo-modified") return { action: "blocked", reason: "destination exists; overwrite forbidden" };
  if (report.state === "live-modified" && entry.sync_direction === "bidirectional") return { action: "blocked", reason: "canonical source exists; overwrite forbidden" };
  return { action: "blocked", reason: report.state };
}

function ensureParent(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function copyEntry(source, destination) {
  const sourceStat = fs.lstatSync(source);
  if (statOrNull(destination)) throw new Error(`refusing to overwrite existing target: ${destination}`);
  if (sourceStat.isSymbolicLink()) {
    ensureParent(destination);
    fs.symlinkSync(fs.readlinkSync(source), destination);
    return;
  }
  if (sourceStat.isDirectory()) {
    ensureParent(destination);
    fs.mkdirSync(destination, { recursive: false });
    for (const child of fs.readdirSync(source)) copyEntry(path.join(source, child), path.join(destination, child));
    return;
  }
  ensureParent(destination);
  fs.copyFileSync(source, destination);
}

function writeDirection(source, destination, action) {
  if (action === "copy-source-to-destination") copyEntry(source, destination);
  if (action === "copy-destination-to-source") copyEntry(destination, source);
}

function routeGraph(manifest) {
  const adjacency = new Map();
  for (const entry of manifest.entries) adjacency.set(entry.id, []);
  for (const route of manifest.routes) adjacency.get(route.from).push(route.to);
  return { nodes: [...adjacency.keys()].sort(), edges: manifest.routes.map((route) => ({ ...route })) };
}

function provenanceMap(manifest, reports) {
  return manifest.entries.map((entry) => {
    const report = reports.find((item) => item.id === entry.id);
    return { id: entry.id, owner: entry.owner, runtime: entry.runtime, layer: entry.layer, always_loaded: entry.always_loaded, source: report?.source ?? entry.source, destination: report?.destination ?? entry.destination, state: report?.state ?? "not-inspected", status: entry.status, sync_direction: entry.sync_direction, provenance: entry.provenance, install_recipe: entry.install_recipe };
  });
}

function inspectAlwaysLoaded(manifest, manifestRoot) {
  return manifest.entries.filter((entry) => entry.always_loaded).map((entry) => {
    const paths = entryPaths(entry, manifest, manifestRoot);
    const source = statOrNull(paths.source);
    const destination = statOrNull(paths.destination);
    const chosen = source?.isFile() ? paths.source : destination?.isFile() ? paths.destination : null;
    if (!chosen) return { id: entry.id, path: displayPath(paths.source, manifestRoot), exists: false, line_count: 0, findings: [{ severity: "error", code: "missing-target", message: "always-loaded target is missing" }] };
    return { id: entry.id, path: displayPath(chosen, manifestRoot), exists: true, ...lintAlwaysLoaded(fs.readFileSync(chosen, "utf8")) };
  });
}

function findDuplicates(scopeReports) {
  const byHash = new Map();
  for (const scope of scopeReports) for (const candidate of scope.candidates) {
    if (!candidate.hash || candidate.size === 0 || candidate.symlink) continue;
    if (!byHash.has(candidate.hash)) byHash.set(candidate.hash, []);
    byHash.get(candidate.hash).push(candidate.path);
  }
  return [...byHash.entries()].filter(([, paths]) => paths.length > 1).map(([hash, paths]) => ({ hash, paths: [...new Set(paths)].sort() })).sort((a, b) => b.paths.length - a.paths.length);
}

function candidateContentConflicts(scopeReports) {
  const items = [];
  for (const scope of scopeReports) for (const candidate of scope.candidates) {
    if (!candidate.path.endsWith("AGENTS.md") && !candidate.path.endsWith("CLAUDE.md") && !candidate.path.endsWith("GEMINI.md")) continue;
    const absolute = candidate.path.startsWith("~") ? path.join(os.homedir(), candidate.path.slice(2)) : candidate.path;
    let content = "";
    try { content = fs.readFileSync(absolute, "utf8"); } catch { continue; }
    if (content.includes("ops-policies.md")) items.push({ type: "broad-policy-import", path: candidate.path, reason: "broad policy import must be replaced by a precise route pointer" });
    if (content.length > 1200 && !content.match(/\b(?:route|load|read|see|manifest|context)\b/i)) items.push({ type: "behavior-bearing-router", path: candidate.path, reason: "instruction surface is large but does not expose a discoverable route; preserve pending review" });
  }
  return items;
}

function buildConflictLedger(manifest, reports, alwaysLoaded, scopeReports) {
  const conflicts = [];
  for (const entry of manifest.entries.filter((item) => item.status === "conflict")) {
    const report = reports.find((item) => item.id === entry.id);
    conflicts.push({ id: `manifest:${entry.id}`, type: "manifest-conflict", path: report?.destination ?? entry.destination, reason: entry.provenance, state: report?.state ?? "not-inspected" });
  }
  for (const report of reports) {
    if (report.source_broken || report.destination_broken) conflicts.push({ id: `broken-link:${report.id}`, type: "broken-link", path: report.source_broken ? report.source : report.destination, reason: "symlink target is missing; preserve and review", state: report.state });
    if (report.manifest_status === "active" && !report.source_exists) conflicts.push({ id: `missing-source:${report.id}`, type: "missing-target", path: report.source, reason: "active canonical source is missing", state: report.state });
  }
  for (const report of reports) if (report.live_only.length > 0) conflicts.push(...report.live_only.map((item) => ({ id: `live-only:${report.id}:${item}`, type: "unknown-live-member", path: `${report.destination}/${item}`, reason: "live payload is not present in canonical source; preserve and review", state: report.state })));
  for (const item of alwaysLoaded.flatMap((report) => report.findings.filter((finding) => finding.severity === "error").map((finding) => ({ id: `always-loaded:${report.id}:${finding.code}`, type: finding.code, path: report.path, reason: finding.message, state: "structural-lint" })))) conflicts.push(item);
  conflicts.push(...candidateContentConflicts(scopeReports).map((item, index) => ({ id: `content:${index + 1}`, ...item, state: "content-scan" })));
  return [...new Map(conflicts.map((item) => [item.id, item])).values()];
}

function writeReport(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content);
}

function markdownLedger(conflicts, metadata) {
  const rows = conflicts.length === 0 ? ["| none | — | — |"] : conflicts.map((item) => `| ${item.type} | ${item.path} | ${item.reason.replaceAll("|", "\\|")} |`);
  return `# Conflict ledger\n\nGenerated by the manifest-aware audit on ${metadata.date}. These entries remain untouched until separately approved.\n\nStatus: **${metadata.status}**\n\n| Type | Path | Reason |\n|---|---|---|\n${rows.join("\n")}\n`;
}

function summaryMarkdown(result) {
  const stateCounts = Object.entries(result.state_counts).map(([state, count]) => `- ${state}: ${count}`).join("\n");
  const lint = result.always_loaded.map((item) => `- ${item.id}: ${item.line_count} lines, ${item.findings.length} finding(s)`).join("\n");
  return `# Instruction audit summary\n\nStatus: **${result.status}**\n\nThe audit is structural and provenance-aware; line count is evidence, not a numeric gate.\n\n## Entry states\n\n${stateCounts || "- none"}\n\n## Always-loaded evidence\n\n${lint || "- none"}\n\n## Inventory\n\n${result.scopes.map((scope) => `- ${scope.id}: ${scope.blocked ?? `${scope.candidates.length} candidate(s)`}`).join("\n")}\n\n## Reports\n\n- [inventory](inventory.json)\n- [provenance map](provenance.json)\n- [duplicate-content report](duplicates.json)\n- [route graph](route-graph.json)\n- [conflict ledger](conflicts.md)\n\n## Conflicts\n\n${result.conflicts.length} ledger item(s). See [conflicts.md](conflicts.md).\n`;
}

export function collectAudit(manifest, manifestRoot, options = {}) {
  const baselines = loadBaselines(manifestRoot);
  const reports = manifest.entries.map((entry) => entryReport(entry, manifest, manifestRoot, baselines));
  const scopes = manifest.inventory_scopes.map((scope) => discoverScope(scope, manifest, manifestRoot, options.allowBroadScan === true));
  const alwaysLoaded = inspectAlwaysLoaded(manifest, manifestRoot);
  const conflicts = buildConflictLedger(manifest, reports, alwaysLoaded, scopes);
  const stateCounts = Object.fromEntries([...new Set(reports.map((report) => report.state))].sort().map((state) => [state, reports.filter((report) => report.state === state).length]));
  const unavailableRuntimes = Object.entries(runtimeAvailability(manifest)).filter(([, command]) => command === null).map(([runtime]) => runtime);
  const cycle = detectRouteCycle(manifest.routes);
  const status = conflicts.length === 0 && unavailableRuntimes.length === 0 && cycle.length === 0 ? "MIGRATION_COMPLETE" : "AUDIT_COMPLETE";
  return { generated_at: new Date().toISOString(), status, state_counts: stateCounts, entries: reports, provenance: provenanceMap(manifest, reports), scopes, always_loaded: alwaysLoaded, duplicates: findDuplicates(scopes), routes: routeGraph(manifest), route_cycle: cycle, unavailable_runtimes: unavailableRuntimes, conflicts };
}

export function writeAuditReports(result, manifestRoot) {
  const auditRoot = path.join(manifestRoot, "audit");
  writeReport(path.join(auditRoot, "inventory.json"), `${JSON.stringify(result, null, 2)}\n`);
  writeReport(path.join(auditRoot, "provenance.json"), `${JSON.stringify(result.provenance, null, 2)}\n`);
  writeReport(path.join(auditRoot, "duplicates.json"), `${JSON.stringify(result.duplicates, null, 2)}\n`);
  writeReport(path.join(auditRoot, "route-graph.json"), `${JSON.stringify(result.routes, null, 2)}\n`);
  writeReport(path.join(auditRoot, "conflicts.md"), markdownLedger(result.conflicts, { date: result.generated_at, status: result.status }));
  writeReport(path.join(auditRoot, "summary.md"), summaryMarkdown(result));
}

export function collectDrift(manifest, manifestRoot) {
  const reports = manifest.entries.map((entry) => entryReport(entry, manifest, manifestRoot, loadBaselines(manifestRoot)));
  return { generated_at: new Date().toISOString(), entries: reports, unknown_live: reports.flatMap((report) => report.live_only.map((item) => ({ entry: report.id, type: "unknown-live-member", path: `${report.destination}/${item}` }))), status: reports.some((report) => report.state !== "equal" && report.state !== "missing-both") ? "DRIFT_PRESENT" : "NO_DRIFT" };
}

export function syncManifest(manifest, manifestRoot, options = {}) {
  const baselines = loadBaselines(manifestRoot);
  const availability = runtimeAvailability(manifest);
  const before = manifest.entries.map((entry) => entryReport(entry, manifest, manifestRoot, baselines));
  const actions = manifest.entries.map((entry) => {
    const report = before.find((item) => item.id === entry.id);
    const decision = canApply(entry, report, availability);
    return { id: entry.id, state: report.state, action: decision.action, reason: decision.reason, source: report.source, destination: report.destination };
  });
  const blocked = actions.filter((action) => action.action === "blocked");
  let applied = false;
  if (options.apply && blocked.length === 0) for (const entry of manifest.entries) {
    const action = actions.find((item) => item.id === entry.id);
    if (!action || !action.action.startsWith("copy-")) continue;
    const paths = entryPaths(entry, manifest, manifestRoot);
    writeDirection(paths.source, paths.destination, action.action);
    const after = entryReport(entry, manifest, manifestRoot, baselines);
    baselines[entry.id] = { hash: after.source_hash, kind: entry.path_kind, updated_at: new Date().toISOString() };
    action.applied = true;
    applied = true;
  }
  if (applied) saveBaselines(manifestRoot, baselines);
  return {
    generated_at: new Date().toISOString(),
    apply: options.apply === true,
    execution_mode: options.apply === true ? "apply" : "dry-run",
    projection_status: "not_projected",
    mutated: applied,
    actions,
    blocked: blocked.length,
    status: blocked.length > 0 ? "SYNC_BLOCKED" : "SYNC_CLEAN"
  };
}

export function doctorManifest(manifest, manifestRoot) {
  const availability = runtimeAvailability(manifest);
  const reports = manifest.entries.map((entry) => entryReport(entry, manifest, manifestRoot, loadBaselines(manifestRoot)));
  const findings = [];
  for (const entry of manifest.entries) {
    const report = reports.find((item) => item.id === entry.id);
    if (entry.status === "active" && !report.source_exists) findings.push({ severity: "error", id: entry.id, message: "active source is missing" });
    if (report.source_broken || report.destination_broken) findings.push({ severity: "error", id: entry.id, message: "symlink target is missing" });
    if (entry.status === "active" && entry.sync_direction !== "report-only" && !report.destination_exists) findings.push({ severity: "error", id: entry.id, message: "active destination is missing" });
    if (entry.status === "conflict") findings.push({ severity: "error", id: entry.id, message: "entry is blocked by the conflict ledger" });
  }
  for (const item of manifest.runtime_commands ?? []) if (!availability[item.runtime]) findings.push({ severity: "warning", id: item.runtime, message: `runtime command ${item.command} is unavailable; ${item.install_recipe}` });
  return { generated_at: new Date().toISOString(), availability, entries: reports, findings, status: findings.some((item) => item.severity === "error") ? "DOCTOR_BLOCKED" : findings.length > 0 ? "DOCTOR_WARNINGS" : "DOCTOR_OK" };
}

export function formatEntryTable(reports) {
  return reports.map((report) => `${report.id.padEnd(28)} ${report.state.padEnd(22)} ${report.manifest_status.padEnd(10)} ${report.source} -> ${report.destination}`).join("\n");
}
