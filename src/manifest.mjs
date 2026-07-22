import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { detectRouteCycle } from "./routing.mjs";

const RUNTIMES = new Set(["codex", "claude", "gemini", "cursor", "antigravity"]);
const STATUS_VALUES = new Set(["active", "conflict", "excluded", "unverified", "planned"]);
const LAYER_VALUES = new Set(["global-invariants", "global-routing", "runtime-adapter", "repo-context", "module-context", "on-demand"]);
const PATH_KIND_VALUES = new Set(["file", "directory", "symlink"]);
const SYNC_VALUES = new Set(["bidirectional", "push-only", "report-only", "none"]);

export function defaultManifestPath() {
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../manifest.yaml");
}

export function parseManifestText(text) {
  try {
    return JSON.parse(text);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`manifest.yaml must be JSON-compatible YAML: ${message}`);
  }
}

export function loadManifest(manifestPath = defaultManifestPath()) {
  const resolved = path.resolve(manifestPath);
  const manifestRoot = path.dirname(resolved);
  const manifest = parseManifestText(fs.readFileSync(resolved, "utf8"));
  validateManifest(manifest);
  return { manifest, manifestPath: resolved, manifestRoot };
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function assertString(value, label, errors) {
  if (typeof value !== "string" || value.trim() === "") errors.push(`${label} must be a non-empty string`);
}

function assertStringArray(value, label, errors) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || item.trim() === "")) errors.push(`${label} must be an array of non-empty strings`);
}

function scanUnsafeManifestValue(value, location, errors) {
  if (typeof value === "string") {
    if (/\/(?:Users|private|var\/folders|tmp|home)\//.test(value)) errors.push(`${location} contains a host-specific absolute path`);
    if (/(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:sk|gh[pousr])-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16})/.test(value)) errors.push(`${location} looks like a credential`);
    if (/(?:password|passwd|secret|token|api[_-]?key|private[_-]?key)\s*[:=]\s*[^\s,}]{8,}/i.test(value)) errors.push(`${location} looks like embedded secret material`);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => scanUnsafeManifestValue(item, `${location}[${index}]`, errors));
    return;
  }
  if (isObject(value)) Object.entries(value).forEach(([key, item]) => scanUnsafeManifestValue(item, `${location}.${key}`, errors));
}

function validatePortablePath(value, label, errors) {
  if (typeof value !== "string") return;
  if (path.isAbsolute(value)) errors.push(`${label} must use a symbolic root token, not an absolute path`);
  if (value.includes("\\") || value.split("/").includes("..")) errors.push(`${label} contains an unsafe path segment`);
  if (value.startsWith("~/")) errors.push(`${label} must use $HOME instead of a home shorthand`);
}

export function validateManifest(manifest) {
  const errors = [];
  if (!isObject(manifest)) errors.push("manifest root must be an object");
  if (manifest?.schema_version !== 1) errors.push("schema_version must be 1");
  assertString(manifest?.manifest_id, "manifest_id", errors);
  if (!isObject(manifest?.roots)) errors.push("roots must be an object");
  for (const [rootName, rootValue] of Object.entries(manifest?.roots ?? {})) {
    assertString(rootValue, `roots.${rootName}`, errors);
    validatePortablePath(rootValue, `roots.${rootName}`, errors);
  }
  if (!Array.isArray(manifest?.entries) || manifest.entries.length === 0) errors.push("entries must be a non-empty array");
  const ids = new Set();
  for (const [index, entry] of (manifest?.entries ?? []).entries()) {
    const label = `entries[${index}]`;
    if (!isObject(entry)) {
      errors.push(`${label} must be an object`);
      continue;
    }
    for (const field of ["id", "source", "destination", "owner", "layer", "path_kind", "sync_direction", "provenance", "install_recipe", "status"]) assertString(entry[field], `${label}.${field}`, errors);
    if (ids.has(entry.id)) errors.push(`${label}.id duplicates ${entry.id}`);
    ids.add(entry.id);
    assertStringArray(entry.runtime, `${label}.runtime`, errors);
    for (const runtime of entry.runtime ?? []) if (!RUNTIMES.has(runtime)) errors.push(`${label}.runtime contains unsupported runtime ${runtime}`);
    if (!LAYER_VALUES.has(entry.layer)) errors.push(`${label}.layer must be one of ${[...LAYER_VALUES].join(", ")}`);
    if (typeof entry.always_loaded !== "boolean") errors.push(`${label}.always_loaded must be boolean`);
    if (!PATH_KIND_VALUES.has(entry.path_kind)) errors.push(`${label}.path_kind must be one of ${[...PATH_KIND_VALUES].join(", ")}`);
    if (!SYNC_VALUES.has(entry.sync_direction)) errors.push(`${label}.sync_direction must be one of ${[...SYNC_VALUES].join(", ")}`);
    if (!STATUS_VALUES.has(entry.status)) errors.push(`${label}.status must be one of ${[...STATUS_VALUES].join(", ")}`);
    if (entry.always_loaded && !new Set(["global-invariants", "global-routing", "runtime-adapter", "repo-context", "module-context"]).has(entry.layer)) errors.push(`${label}.always_loaded cannot use layer ${entry.layer}`);
    validatePortablePath(entry.source, `${label}.source`, errors);
    validatePortablePath(entry.destination, `${label}.destination`, errors);
  }
  if (!Array.isArray(manifest?.inventory_scopes)) errors.push("inventory_scopes must be an array");
  for (const [index, scope] of (manifest?.inventory_scopes ?? []).entries()) {
    const label = `inventory_scopes[${index}]`;
    if (!isObject(scope)) {
      errors.push(`${label} must be an object`);
      continue;
    }
    assertString(scope.id, `${label}.id`, errors);
    assertString(scope.root, `${label}.root`, errors);
    assertStringArray(scope.patterns, `${label}.patterns`, errors);
    assertStringArray(scope.excludes, `${label}.excludes`, errors);
    assertStringArray(scope.exclude_patterns ?? [], `${label}.exclude_patterns`, errors);
    if (!Number.isInteger(scope.max_depth) || scope.max_depth < 0 || scope.max_depth > 12) errors.push(`${label}.max_depth must be an integer from 0 to 12`);
  }
  if (!Array.isArray(manifest?.routes)) errors.push("routes must be an array");
  const routeIds = new Set();
  for (const [index, route] of (manifest?.routes ?? []).entries()) {
    const label = `routes[${index}]`;
    if (!isObject(route)) {
      errors.push(`${label} must be an object`);
      continue;
    }
    for (const field of ["id", "from", "to", "when", "load", "reason"]) assertString(route[field], `${label}.${field}`, errors);
    if (routeIds.has(route.id)) errors.push(`${label}.id duplicates ${route.id}`);
    routeIds.add(route.id);
    if (!ids.has(route.from)) errors.push(`${label}.from references unknown entry ${route.from}`);
    if (!ids.has(route.to)) errors.push(`${label}.to references unknown entry ${route.to}`);
  }
  scanUnsafeManifestValue(manifest, "manifest", errors);
  const cycle = detectRouteCycle(manifest?.routes ?? []);
  if (cycle.length > 0) errors.push(`route graph contains a cycle: ${cycle.join(" -> ")}`);
  if (errors.length > 0) throw new Error(`Manifest validation failed:\n- ${errors.join("\n- ")}`);
  return true;
}

export function expandPath(rawPath, manifest, manifestRoot) {
  if (typeof rawPath !== "string") throw new Error("path must be a string");
  const pathErrors = [];
  validatePortablePath(rawPath, "path", pathErrors);
  if (pathErrors.length > 0) throw new Error(pathErrors.join("; "));
  const values = { HOME: os.homedir(), MANIFEST_ROOT: manifestRoot };
  for (const [key, value] of Object.entries(manifest.roots ?? {})) values[key] = value;
  let expanded = rawPath;
  for (let pass = 0; pass < 8; pass += 1) {
    const next = expanded.replace(/\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)/g, (_match, braced, bare) => {
      const key = braced ?? bare;
      if (!(key in values)) throw new Error(`unknown manifest path variable $${key}`);
      return values[key];
    });
    if (next === expanded) break;
    expanded = next;
  }
  if (expanded.includes("$")) throw new Error(`unexpanded manifest path variable in ${rawPath}`);
  if (expanded.startsWith("~/")) expanded = path.join(os.homedir(), expanded.slice(2));
  return path.resolve(path.isAbsolute(expanded) ? expanded : path.join(manifestRoot, expanded));
}
