import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { expandPath } from "./manifest.mjs";
import { commandAvailable } from "./runtime.mjs";

const DEFAULT_IGNORES = new Set([".git", "node_modules", ".pnpm-store", ".cache", "cache", "caches", "dist", "build", ".build", ".next", ".turbo", ".vercel", "coverage", "target", "vendor", "fixtures", ".agent-config-state", "audit"]);
const MAX_WALK_ENTRIES = 40000;

export function displayPath(filePath, manifestRoot) {
  const resolved = path.resolve(filePath);
  const home = os.homedir();
  if (resolved === home || resolved.startsWith(`${home}${path.sep}`)) return `~${resolved.slice(home.length)}`;
  if (resolved === manifestRoot || resolved.startsWith(`${manifestRoot}${path.sep}`)) return `$MANIFEST_ROOT${resolved.slice(manifestRoot.length)}`;
  return resolved;
}

export function statOrNull(filePath) {
  try {
    return fs.lstatSync(filePath);
  } catch (error) {
    if (error && typeof error === "object" && error.code === "ENOENT") return null;
    throw error;
  }
}

function digestBuffer(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function digestSymlink(filePath) {
  return digestBuffer(Buffer.from(`symlink:${fs.readlinkSync(filePath)}`));
}

function relativeDepth(relativePath) {
  if (relativePath === "") return 0;
  return relativePath.split(path.sep).length;
}

function shouldIgnore(relativePath, excludes = []) {
  const normalized = relativePath.split(path.sep).join("/");
  const segments = normalized.split("/");
  return [...DEFAULT_IGNORES, ...excludes].some((item) => normalized === item || normalized.startsWith(`${item}/`) || segments.includes(item));
}

function walkFiles(root, options = {}) {
  const maxDepth = options.maxDepth ?? 12;
  const excludes = options.excludes ?? [];
  const results = [];
  const queue = [{ absolute: root, relative: "" }];
  while (queue.length > 0) {
    const current = queue.shift();
    const stat = statOrNull(current.absolute);
    if (!stat) continue;
    if (stat.isSymbolicLink() || stat.isFile()) {
      results.push(current);
      continue;
    }
    if (!stat.isDirectory() || relativeDepth(current.relative) >= maxDepth) continue;
    let children = [];
    try {
      children = fs.readdirSync(current.absolute, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const child of children) {
      const relative = current.relative ? path.join(current.relative, child.name) : child.name;
      if (shouldIgnore(relative, excludes)) continue;
      queue.push({ absolute: path.join(current.absolute, child.name), relative });
      if (queue.length + results.length > MAX_WALK_ENTRIES) throw new Error(`walk limit exceeded under ${root}; narrow the manifest scope`);
    }
  }
  return results;
}

function snapshotFile(filePath, stat) {
  if (stat.isSymbolicLink()) {
    const target = fs.readlinkSync(filePath);
    return { kind: "symlink", target, broken: !fs.existsSync(filePath), hash: digestSymlink(filePath), size: 0 };
  }
  if (stat.isFile()) return { kind: "file", hash: digestBuffer(fs.readFileSync(filePath)), size: stat.size };
  return null;
}

export function snapshotPath(filePath) {
  const stat = statOrNull(filePath);
  if (!stat) return null;
  const direct = snapshotFile(filePath, stat);
  if (direct) return direct;
  if (!stat.isDirectory()) return { kind: "other", hash: null, size: stat.size };
  const files = walkFiles(filePath).map((item) => {
    const childStat = statOrNull(item.absolute);
    const child = childStat ? snapshotFile(item.absolute, childStat) : null;
    return { path: item.relative.split(path.sep).join("/"), ...(child ?? { kind: "missing", hash: null, size: 0 }) };
  }).sort((a, b) => a.path.localeCompare(b.path));
  const hash = digestBuffer(Buffer.from(files.map((item) => `${item.path}\0${item.kind}\0${item.hash ?? ""}`).join("\n")));
  return { kind: "directory", hash, size: files.reduce((total, item) => total + item.size, 0), files };
}

function globRegExp(pattern) {
  let source = "^";
  for (let index = 0; index < pattern.length; index += 1) {
    const char = pattern[index];
    if (char === "*" && pattern[index + 1] === "*") {
      if (pattern[index + 2] === "/") {
        source += "(?:.*/)?";
        index += 2;
      } else {
        source += ".*";
        index += 1;
      }
    } else if (char === "*") source += "[^/]*";
    else if (char === "?") source += "[^/]";
    else source += /[\\^$+{}()|.\[\]]/.test(char) ? `\\${char}` : char;
  }
  return new RegExp(`${source}$`);
}

function matchesPattern(relative, pattern) {
  const normalized = relative.split(path.sep).join("/");
  const effectivePattern = pattern.includes("/") && !pattern.startsWith("**/") ? `**/${pattern}` : pattern;
  const candidate = effectivePattern.includes("/") ? normalized : path.posix.basename(normalized);
  return globRegExp(effectivePattern).test(candidate);
}

function discoverWithRipgrep(root, scope) {
  const rg = commandAvailable("rg");
  if (!rg) return null;
  const args = ["--files", "--hidden", "--no-ignore"];
  for (const pattern of scope.patterns) args.push("--glob", pattern.startsWith("**/") ? pattern : `**/${pattern}`);
  for (const pattern of scope.exclude_patterns ?? []) args.push("--glob", `!${pattern.startsWith("**/") ? pattern : `**/${pattern}`}`);
  for (const exclude of scope.excludes) args.push("--glob", `!**/${exclude.replace(/^\*\*\//, "").replace(/\/$/, "")}/**`);
  const result = spawnSync(rg, args, { cwd: root, encoding: "utf8", maxBuffer: 12 * 1024 * 1024 });
  if (result.status !== 0 && result.status !== 1) return null;
  return (result.stdout ?? "").split(/\r?\n/).filter(Boolean).map((relative) => ({ absolute: path.resolve(root, relative), relative }));
}

function isExcludedRelative(relative, excludes = []) {
  const normalized = relative.split(path.sep).join("/");
  return excludes.some((exclude) => {
    const normalizedExclude = exclude.replace(/^\*\*\//, "").replace(/\/$/, "");
    if (!normalizedExclude) return false;
    return normalized === normalizedExclude || normalized.startsWith(`${normalizedExclude}/`) || normalized.split("/").includes(normalizedExclude) || (normalizedExclude.includes("/") && normalized.includes(`${normalizedExclude}/`));
  });
}

export function discoverScope(scope, manifest, manifestRoot, allowBroadScan) {
  const root = expandPath(scope.root, manifest, manifestRoot);
  if (scope.root === "$HOME" && !allowBroadScan) return { id: scope.id, root: displayPath(root, manifestRoot), blocked: "broad home scan requires --allow-broad-scan", candidates: [], excluded: [] };
  const discovered = discoverWithRipgrep(root, scope) ?? walkFiles(root, { maxDepth: scope.max_depth, excludes: scope.excludes });
  const files = discovered.filter((item) => relativeDepth(item.relative) <= scope.max_depth && !isExcludedRelative(item.relative, scope.excludes));
  const candidates = files.filter((item) => scope.patterns.some((pattern) => matchesPattern(item.relative, pattern)) && !(scope.exclude_patterns ?? []).some((pattern) => matchesPattern(item.relative, pattern))).map((item) => {
    const stat = statOrNull(item.absolute);
    return { path: displayPath(item.absolute, manifestRoot), relative: item.relative.split(path.sep).join("/"), hash: snapshotPath(item.absolute)?.hash ?? null, size: stat?.size ?? 0, symlink: stat?.isSymbolicLink() ?? false };
  });
  return { id: scope.id, root: displayPath(root, manifestRoot), blocked: null, candidates, excluded: scope.excludes };
}

export function loadBaselines(manifestRoot) {
  try {
    return JSON.parse(fs.readFileSync(path.join(manifestRoot, ".agent-config-state", "baselines.json"), "utf8"));
  } catch {
    return {};
  }
}

export function saveBaselines(manifestRoot, baselines) {
  const directory = path.join(manifestRoot, ".agent-config-state");
  fs.mkdirSync(directory, { recursive: true });
  fs.writeFileSync(path.join(directory, "baselines.json"), `${JSON.stringify(baselines, null, 2)}\n`);
}

export function entryPaths(entry, manifest, manifestRoot) {
  return { source: expandPath(entry.source, manifest, manifestRoot), destination: expandPath(entry.destination, manifest, manifestRoot) };
}

export function compareSnapshots(source, destination, baseline = null) {
  if (!source && !destination) return "missing-both";
  if (source && !destination) return "repo-only";
  if (!source && destination) return "live-only";
  if (source.hash === destination.hash && source.kind === destination.kind) return "equal";
  if (baseline?.hash) {
    const sourceIsBaseline = source.hash === baseline.hash;
    const destinationIsBaseline = destination.hash === baseline.hash;
    if (!sourceIsBaseline && destinationIsBaseline) return "repo-modified";
    if (sourceIsBaseline && !destinationIsBaseline) return "live-modified";
    if (!sourceIsBaseline && !destinationIsBaseline) return "both-modified";
  }
  return "diverged-no-baseline";
}

export function entryReport(entry, manifest, manifestRoot, baselines) {
  const paths = entryPaths(entry, manifest, manifestRoot);
  const sourceStat = statOrNull(paths.source);
  const destinationStat = statOrNull(paths.destination);
  const inventoryOnly = entry.inventory_only === true;
  const source = inventoryOnly ? (sourceStat ? { kind: entry.path_kind, hash: null, size: sourceStat.size } : null) : snapshotPath(paths.source);
  const destination = inventoryOnly ? (destinationStat ? { kind: entry.path_kind, hash: null, size: destinationStat.size } : null) : snapshotPath(paths.destination);
  const samePath = paths.source === paths.destination;
  const baseline = baselines[entry.id] ?? null;
  const state = inventoryOnly ? (source || destination ? "inventory-only" : "missing-both") : samePath ? (source ? "equal" : "missing-both") : compareSnapshots(source, destination, baseline);
  const sourceFiles = source?.kind === "directory" && source.files ? new Map(source.files.map((item) => [item.path, item])) : new Map();
  const destinationFiles = destination?.kind === "directory" && destination.files ? new Map(destination.files.map((item) => [item.path, item])) : new Map();
  const sourceOnly = [...sourceFiles.keys()].filter((key) => !destinationFiles.has(key)).sort();
  const liveOnly = [...destinationFiles.keys()].filter((key) => !sourceFiles.has(key)).sort();
  const changedMembers = [...sourceFiles.keys()].filter((key) => destinationFiles.has(key) && sourceFiles.get(key)?.hash !== destinationFiles.get(key)?.hash).sort();
  return { id: entry.id, manifest_status: entry.status, sync_direction: entry.sync_direction, path_kind: entry.path_kind, source: displayPath(paths.source, manifestRoot), destination: displayPath(paths.destination, manifestRoot), source_exists: Boolean(source), destination_exists: Boolean(destination), source_broken: source?.broken === true, destination_broken: destination?.broken === true, source_hash: source?.hash ?? null, destination_hash: destination?.hash ?? null, baseline_hash: baseline?.hash ?? null, state, live_empty: destination?.kind === "file" && destination.size === 0, source_only: sourceOnly, live_only: liveOnly, changed_members: changedMembers, provenance: entry.provenance, install_recipe: entry.install_recipe, runtime: entry.runtime };
}
