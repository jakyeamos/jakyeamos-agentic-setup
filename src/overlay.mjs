import fs from "node:fs";
import path from "node:path";
import { expandPath } from "./manifest.mjs";

export const PRIVATE_OVERLAY_SCHEMA_VERSION = "jas-private-overlay/v2";
export const PRIVATE_OVERLAY_SCHEMA_V1 = "jas-private-overlay/v1";

const OVERLAY_VISIBILITY = "private-overlay";
const ID_PATTERN = /^[a-z0-9][a-z0-9-]+$/;
const TARGETS = new Set(["generic", "codex", "claude", "gemini", "cursor", "antigravity", "copilot"]);
const PRIVATE_KINDS = new Set(["skill", "workflow", "prompt", "advice", "guardrail", "adapter", "other"]);
const PRIVATE_MATURITIES = new Set(["experimental", "beta", "stable", "reference"]);
const ELIGIBLE_ASSET_CLASSES = new Set(["portable", "adapter"]);
const ELIGIBLE_INSTALL_MODES = new Set(["copy", "stage"]);
const PRIVATE_PACKAGE_REF = /^artifact:[a-z0-9][a-z0-9:_-]*$/;

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function readJsonObject(filePath, label) {
  let value;
  try {
    value = JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    throw new Error(`unable to read ${label} input`);
  }
  if (!isObject(value)) throw new Error(`${label} must be a JSON object`);
  return value;
}

function assertKnownFields(value, fields, label) {
  for (const field of Object.keys(value)) if (!fields.has(field)) throw new Error(`${label} contains an unsupported field`);
}

function assertText(value, label) {
  if (typeof value !== "string" || value.trim() === "") throw new Error(`${label} must be a non-empty string`);
  return value.trim();
}

function assertSafeId(value, label) {
  const text = assertText(value, label);
  if (!ID_PATTERN.test(text)) throw new Error(`${label} must be a safe identifier`);
  return text;
}

function assertTargets(value, label) {
  if (!Array.isArray(value) || value.length === 0 || value.some((item) => typeof item !== "string" || !TARGETS.has(item))) {
    throw new Error(`${label} must contain supported target names`);
  }
  const targets = [...new Set(value)];
  if (targets.length !== value.length) throw new Error(`${label} must not contain duplicates`);
  return targets.sort();
}

function assertRelativePath(value, label) {
  const text = assertText(value, label);
  const candidate = path.posix.normalize(text);
  if (path.posix.isAbsolute(text) || text.includes("\\") || candidate === "." || candidate === ".." || candidate.startsWith("../") || text.split("/").includes("..")) {
    throw new Error(`${label} must be a safe relative path`);
  }
  return candidate;
}

function assertRelativePathList(value, label) {
  if (!Array.isArray(value) || value.length === 0) throw new Error(`${label} must contain relative paths`);
  const paths = value.map((item, index) => assertRelativePath(item, `${label}[${index}]`));
  if (new Set(paths).size !== paths.length) throw new Error(`${label} must not contain duplicates`);
  return paths;
}

function assertSymbolicDestination(value, label, baseManifest, manifestRoot) {
  const destination = assertText(value, label);
  if (!/^\$(?:\{[A-Za-z_][A-Za-z0-9_]*\}|[A-Za-z_][A-Za-z0-9_]*)(?:\/|$)/.test(destination)) {
    throw new Error(`${label} must begin with a symbolic root token`);
  }
  try {
    expandPath(destination, baseManifest, manifestRoot);
  } catch {
    throw new Error(`${label} must be a safe symbolic path`);
  }
  return destination;
}

function assertPrivateDestination(value, label, baseManifest, manifestRoot) {
  const destination = assertSymbolicDestination(value, label, baseManifest, manifestRoot);
  if (!/^\$(?:\{HOME\}|HOME)(?:\/|$)/.test(destination)) {
    throw new Error(`${label} must be anchored to $HOME for private installation`);
  }
  return destination;
}

function validatePrivateAsset(value, index, baseManifest, manifestRoot) {
  const label = `private_assets[${index}]`;
  if (!isObject(value)) throw new Error(`${label} must be an object`);
  assertKnownFields(value, new Set(["id", "kind", "title", "summary", "maturity", "supported_targets", "package_ref", "package_dir", "entrypoints", "files", "install"]), label);
  const id = assertSafeId(value.id, `${label}.id`);
  const kind = assertText(value.kind, `${label}.kind`);
  if (!PRIVATE_KINDS.has(kind)) throw new Error(`${label}.kind is unsupported`);
  const title = assertText(value.title, `${label}.title`);
  const summary = assertText(value.summary, `${label}.summary`);
  const maturity = assertText(value.maturity, `${label}.maturity`);
  if (!PRIVATE_MATURITIES.has(maturity)) throw new Error(`${label}.maturity is unsupported`);
  const supportedTargets = assertTargets(value.supported_targets, `${label}.supported_targets`);
  const packageRef = assertText(value.package_ref, `${label}.package_ref`);
  if (!PRIVATE_PACKAGE_REF.test(packageRef)) throw new Error(`${label}.package_ref must be a sanitized artifact reference`);
  const packageDir = assertRelativePath(value.package_dir, `${label}.package_dir`);
  const files = assertRelativePathList(value.files, `${label}.files`);
  const entrypoints = assertRelativePathList(value.entrypoints, `${label}.entrypoints`);
  if (entrypoints.some((entrypoint) => !files.includes(entrypoint))) throw new Error(`${label}.entrypoints must be listed in files`);
  if (!isObject(value.install)) throw new Error(`${label}.install must be an object`);
  assertKnownFields(value.install, new Set(["mode", "destination"]), `${label}.install`);
  const mode = assertText(value.install.mode, `${label}.install.mode`);
  if (!ELIGIBLE_INSTALL_MODES.has(mode)) throw new Error(`${label}.install.mode is unsupported`);
  const destination = assertPrivateDestination(value.install.destination, `${label}.install.destination`, baseManifest, manifestRoot);
  return { id, kind, title, summary, maturity, supported_targets: supportedTargets, package_ref: packageRef, package_dir: packageDir, entrypoints, files, install: { mode, destination } };
}

function validateOverlay(overlay, baseManifest, manifestRoot) {
  const isV1 = overlay.schema_version === PRIVATE_OVERLAY_SCHEMA_V1;
  const isV2 = overlay.schema_version === PRIVATE_OVERLAY_SCHEMA_VERSION;
  if (!isV1 && !isV2) throw new Error("private overlay schema_version is not supported");
  const allowedFields = new Set(["schema_version", "visibility", "overlay_id", "base_workbench_id", "references"]);
  if (isV2) allowedFields.add("private_assets");
  assertKnownFields(overlay, allowedFields, "private overlay");
  if (overlay.visibility !== OVERLAY_VISIBILITY) throw new Error("private overlay visibility is not supported");
  const overlayId = assertSafeId(overlay.overlay_id, "overlay_id");
  const baseWorkbenchId = assertSafeId(overlay.base_workbench_id, "base_workbench_id");
  if (!Array.isArray(overlay.references) || overlay.references.length === 0) throw new Error("references must be a non-empty array");
  const referenceIds = new Set();
  const assetIds = new Set();
  let enabledCount = 0;
  const references = overlay.references.map((value, index) => {
    const label = `references[${index}]`;
    if (!isObject(value)) throw new Error(`${label} must be an object`);
    assertKnownFields(value, new Set(["id", "asset_id", "enabled", "targets", "destination"]), label);
    const id = assertSafeId(value.id, `${label}.id`);
    const assetId = assertSafeId(value.asset_id, `${label}.asset_id`);
    if (referenceIds.has(id)) throw new Error(`${label}.id duplicates another reference`);
    if (assetIds.has(assetId)) throw new Error(`${label}.asset_id duplicates another reference`);
    referenceIds.add(id);
    assetIds.add(assetId);
    if (typeof value.enabled !== "boolean") throw new Error(`${label}.enabled must be boolean`);
    if (value.enabled) enabledCount += 1;
    const targets = assertTargets(value.targets, `${label}.targets`);
    let destination = null;
    if (value.destination !== undefined) destination = assertSymbolicDestination(value.destination, `${label}.destination`, baseManifest, manifestRoot);
    return { id, asset_id: assetId, enabled: value.enabled, targets, destination };
  });
  if (enabledCount === 0) throw new Error("at least one overlay reference must be enabled");
  const privateAssets = new Map();
  if (isV2) {
    if (!Array.isArray(overlay.private_assets) || overlay.private_assets.length === 0) throw new Error("v2 private overlay requires private_assets");
    for (const [index, value] of overlay.private_assets.entries()) {
      const asset = validatePrivateAsset(value, index, baseManifest, manifestRoot);
      if (privateAssets.has(asset.id)) throw new Error(`private_assets[${index}].id duplicates another private asset`);
      privateAssets.set(asset.id, asset);
    }
  }
  return { schema_version: overlay.schema_version, overlay_id: overlayId, base_workbench_id: baseWorkbenchId, references: references.sort((a, b) => a.id.localeCompare(b.id)), private_assets: privateAssets };
}

function validateCatalog(catalog) {
  if (catalog.schema_version !== 1) throw new Error("public catalog schema_version is not supported");
  if (!isObject(catalog.workbench)) throw new Error("public catalog workbench must be an object");
  const workbenchId = assertSafeId(catalog.workbench.id, "public catalog workbench.id");
  if (!Array.isArray(catalog.assets) || catalog.assets.length === 0) throw new Error("public catalog assets must be a non-empty array");
  const assets = new Map();
  for (const [index, value] of catalog.assets.entries()) {
    const label = `public catalog assets[${index}]`;
    if (!isObject(value)) throw new Error(`${label} must be an object`);
    const id = assertSafeId(value.id, `${label}.id`);
    if (assets.has(id)) throw new Error(`${label}.id duplicates another asset`);
    if (!ELIGIBLE_ASSET_CLASSES.has(value.asset_class)) {
      assets.set(id, value);
      continue;
    }
    if (typeof value.title !== "string" || value.title.trim() === "") throw new Error(`${label}.title must be a non-empty string`);
    if (!Array.isArray(value.supported_targets) || value.supported_targets.length === 0 || value.supported_targets.some((target) => !TARGETS.has(target))) {
      throw new Error(`${label}.supported_targets contains an unsupported target`);
    }
    if (!isObject(value.provenance) || value.provenance.redistribution !== "allowed") {
      throw new Error(`${label}.provenance does not permit redistribution`);
    }
    if (!isObject(value.install) || !ELIGIBLE_INSTALL_MODES.has(value.install.mode)) {
      throw new Error(`${label}.install.mode is not eligible for an overlay`);
    }
    if (!Array.isArray(value.files) || value.files.length === 0) throw new Error(`${label}.files must be non-empty for an installable asset`);
    value.files.forEach((file, fileIndex) => assertRelativePath(file, `${label}.files[${fileIndex}]`));
    if (!assertRelativePath(value.install.destination, `${label}.install.destination`)) throw new Error(`${label}.install.destination is invalid`);
    assets.set(id, value);
  }
  return { workbench_id: workbenchId, assets };
}

function validatedInputs({ overlayPath, catalogPath, baseManifest, manifestRoot }) {
  if (typeof overlayPath !== "string" || overlayPath.trim() === "") throw new Error("overlay requires a path");
  if (typeof catalogPath !== "string" || catalogPath.trim() === "") throw new Error("overlay requires a public catalog path");
  if (!isObject(baseManifest) || typeof manifestRoot !== "string" || manifestRoot.trim() === "") throw new Error("overlay requires a validated base manifest");
  const overlay = validateOverlay(loadPrivateOverlay(overlayPath), baseManifest, manifestRoot);
  const catalog = validateCatalog(loadPublicCatalog(catalogPath));
  if (overlay.base_workbench_id !== catalog.workbench_id) throw new Error("overlay base_workbench_id does not match the public catalog");
  return { overlay, catalog };
}

function selectAsset(reference, overlay, catalog) {
  const privateAsset = overlay.private_assets.get(reference.asset_id);
  if (privateAsset) return { source_kind: "private-package", asset: privateAsset };
  const asset = catalog.assets.get(reference.asset_id);
  if (!asset) throw new Error("overlay references an unknown public asset");
  if (!ELIGIBLE_ASSET_CLASSES.has(asset.asset_class)) throw new Error("overlay references an asset that is not eligible for personal use");
  return { source_kind: "public-catalog", asset };
}

function assertReferenceSupport(reference, asset) {
  const supportedTargets = new Set(asset.supported_targets);
  if (reference.targets.some((target) => !supportedTargets.has(target))) throw new Error("overlay target is not supported by the referenced asset");
}

function resolvedAssets(overlay, catalog) {
  const assets = [];
  for (const reference of overlay.references) {
    const selected = selectAsset(reference, overlay, catalog);
    assertReferenceSupport(reference, selected.asset);
    if (!reference.enabled) continue;
    const asset = selected.asset;
    assets.push(selected.source_kind === "private-package"
      ? { id: asset.id, title: asset.title, summary: asset.summary, asset_class: "private", kind: asset.kind, maturity: asset.maturity, supported_targets: [...asset.supported_targets].sort(), install_mode: asset.install.mode, destination: reference.destination ?? asset.install.destination, source_kind: selected.source_kind, package_ref: asset.package_ref, package_dir: asset.package_dir, files: [...asset.files], entrypoints: [...asset.entrypoints] }
      : { id: asset.id, title: asset.title, asset_class: asset.asset_class, maturity: asset.maturity, supported_targets: [...asset.supported_targets].sort(), install_mode: asset.install.mode });
  }
  return assets.sort((a, b) => a.id.localeCompare(b.id));
}

export function loadPrivateOverlay(overlayPath) {
  return readJsonObject(overlayPath, "private overlay");
}

export function loadPublicCatalog(catalogPath) {
  return readJsonObject(catalogPath, "public catalog");
}

export function resolvePrivateOverlay({ overlayPath, catalogPath, baseManifest, manifestRoot }) {
  const { overlay, catalog } = validatedInputs({ overlayPath, catalogPath, baseManifest, manifestRoot });
  return {
    schema_version: overlay.schema_version,
    status: "OVERLAY_VALID",
    visibility: OVERLAY_VISIBILITY,
    overlay_id: overlay.overlay_id,
    base_workbench_id: overlay.base_workbench_id,
    references: overlay.references,
    assets: resolvedAssets(overlay, catalog),
    catalog: "public-catalog",
    mutated: false
  };
}

function rootSafe(root, label, allowHome = false) {
  if (typeof root !== "string" || root.trim() === "") throw new Error(`${label} must be a disposable non-home directory`);
  const resolved = path.resolve(root);
  const home = typeof process.env.HOME === "string" && process.env.HOME.trim() !== "" ? path.resolve(process.env.HOME) : null;
  if (allowHome && (!home || resolved !== home)) throw new Error(`${label} --allow-home requires the real home directory`);
  if (resolved === path.parse(resolved).root || (resolved === home && !allowHome)) throw new Error(`${label} must be a disposable non-home directory`);
  const existing = existingPath(resolved);
  if (home && fs.realpathSync(existing) === home && !allowHome) throw new Error(`${label} must not resolve to the home directory`);
  return resolved;
}

function pathExists(candidate) {
  try {
    fs.lstatSync(candidate);
    return true;
  } catch (error) {
    if (error && typeof error === "object" && error.code === "ENOENT") return false;
    throw error;
  }
}

function existingPath(candidate) {
  let cursor = path.resolve(candidate);
  while (!pathExists(cursor) && cursor !== path.dirname(cursor)) cursor = path.dirname(cursor);
  return cursor;
}

function withinRoot(root, candidate, label) {
  const resolvedRoot = path.resolve(root);
  const resolvedCandidate = path.resolve(candidate);
  const relative = path.relative(resolvedRoot, resolvedCandidate);
  if (relative === ".." || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) throw new Error(`${label} escapes its root`);
  return resolvedCandidate;
}

function existingAncestorWithin(root, candidate, label) {
  const resolvedRoot = path.resolve(root);
  const rootCursor = existingPath(resolvedRoot);
  const candidateCursor = existingPath(path.dirname(path.resolve(candidate)));
  try {
    withinRoot(fs.realpathSync(rootCursor), fs.realpathSync(candidateCursor), label);
  } catch {
    throw new Error(`${label} has an unsafe existing parent`);
  }
}

function targetDestination(rawDestination, targetRoot, baseManifest, manifestRoot, label) {
  if (typeof rawDestination !== "string") throw new Error(`${label} must have an install destination`);
  const destination = assertSymbolicDestination(rawDestination, label, baseManifest, manifestRoot);
  const match = destination.match(/^\$(?:\{HOME\}|HOME)(?:\/(.*))?$/);
  if (!match) throw new Error(`${label} must be anchored to $HOME for overlay installation`);
  const resolved = withinRoot(targetRoot, path.join(targetRoot, match[1] ?? ""), label);
  existingAncestorWithin(targetRoot, resolved, label);
  return resolved;
}

function publicInstallDestination(asset, reference, targetRoot, baseManifest, manifestRoot) {
  if (reference.destination) return targetDestination(reference.destination, targetRoot, baseManifest, manifestRoot, `reference ${reference.id}.destination`);
  return withinRoot(targetRoot, path.join(targetRoot, assertRelativePath(asset.install.destination, `asset ${asset.id}.install.destination`)), `asset ${asset.id}.install.destination`);
}

function privateSourceRoot(privateRoot, asset) {
  if (!privateRoot) throw new Error("private overlay installation requires --private-root");
  const root = path.resolve(privateRoot);
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) throw new Error("private overlay --private-root must be an existing directory");
  const packageRoot = withinRoot(root, path.join(root, asset.package_dir), `private asset ${asset.id}.package_dir`);
  if (!fs.existsSync(packageRoot) || !fs.statSync(packageRoot).isDirectory()) throw new Error(`private asset ${asset.id} package is missing`);
  try {
    withinRoot(fs.realpathSync(root), fs.realpathSync(packageRoot), `private asset ${asset.id}.package_dir`);
  } catch {
    throw new Error(`private asset ${asset.id} package escapes --private-root`);
  }
  return packageRoot;
}

function sourceRootForPublic(asset, manifestRoot) {
  return path.resolve(manifestRoot);
}

function installRelativePath(asset, source) {
  const pathMap = isObject(asset.install) && isObject(asset.install.path_map) ? asset.install.path_map : {};
  if (typeof pathMap[source] === "string") return assertRelativePath(pathMap[source], `asset ${asset.id}.install.path_map.${source}`);
  const sourceRoot = path.posix.dirname(asset.entrypoints?.[0] ?? asset.files?.[0] ?? ".");
  const relative = path.posix.relative(sourceRoot, source);
  if (relative && !relative.split("/").includes("..")) return assertRelativePath(relative, `asset ${asset.id}.files`);
  return assertRelativePath(path.posix.basename(source), `asset ${asset.id}.files`);
}

function sourceAction(sourceRoot, file, displayRoot, destinationRoot, relativeDestination, label) {
  const source = withinRoot(sourceRoot, path.join(sourceRoot, file), `${label}.source`);
  let stat;
  try {
    stat = fs.lstatSync(source);
  } catch {
    return { source_path: null, action: { source: path.posix.join(displayRoot, file), destination: path.join(destinationRoot, relativeDestination), status: "missing-source" } };
  }
  if (!stat.isFile() || stat.isSymbolicLink()) throw new Error(`${label}.source must be a regular file`);
  const destination = withinRoot(destinationRoot, path.join(destinationRoot, relativeDestination), `${label}.destination`);
  existingAncestorWithin(destinationRoot, destination, `${label}.destination`);
  return { source_path: source, action: { source: path.posix.join(displayRoot, file), destination, status: pathExists(destination) ? "exists" : "would-copy" } };
}

function buildInstallPlan({ overlay, catalog, baseManifest, manifestRoot, privateRoot, targetRoot, apply, allowHome = false }) {
  const root = rootSafe(targetRoot, "overlay installation root", allowHome);
  const actions = [];
  const sourcePaths = [];
  for (const reference of overlay.references) {
    if (!reference.enabled) continue;
    const selected = selectAsset(reference, overlay, catalog);
    assertReferenceSupport(reference, selected.asset);
    const asset = selected.asset;
    const isPrivate = selected.source_kind === "private-package";
    const sourceRoot = isPrivate ? privateSourceRoot(privateRoot, asset) : sourceRootForPublic(asset, manifestRoot);
    const destinationRoot = isPrivate
      ? targetDestination(reference.destination ?? asset.install.destination, root, baseManifest, manifestRoot, `private asset ${asset.id}.destination`)
      : publicInstallDestination(asset, reference, root, baseManifest, manifestRoot);
    const files = Array.isArray(asset.files) ? asset.files : [];
    const displayRoot = isPrivate ? path.posix.join("$PRIVATE_ROOT", asset.package_dir) : "$JAS_ROOT";
    const sourceFiles = files.map((file) => {
      const normalizedFile = assertRelativePath(file, `asset ${asset.id}.files`);
      const relativeDestination = isPrivate ? normalizedFile : installRelativePath(asset, normalizedFile);
      const result = sourceAction(sourceRoot, normalizedFile, displayRoot, destinationRoot, relativeDestination, `asset ${asset.id}`);
      sourcePaths.push(result.source_path);
      return result.action;
    });
    actions.push(...sourceFiles.map((action) => ({ ...action, asset_id: asset.id, reference_id: reference.id })));
  }
  const hasBlocked = actions.some((action) => ["exists", "missing-source"].includes(action.status));
  const status = hasBlocked ? "OVERLAY_INSTALL_BLOCKED" : "OVERLAY_INSTALL_READY";
  return { schema_version: overlay.schema_version, status, visibility: OVERLAY_VISIBILITY, overlay_id: overlay.overlay_id, base_workbench_id: overlay.base_workbench_id, root, private_assets: [...overlay.private_assets.keys()].sort(), actions, dry_run: !apply, mutated: false, _source_paths: sourcePaths };
}

function applyInstallPlan(plan) {
  if (plan.status !== "OVERLAY_INSTALL_READY") return plan;
  for (const [index, action] of plan.actions.entries()) {
    const source = plan._source_paths[index];
    const destination = path.resolve(String(action.destination));
    if (!source || !fs.existsSync(source) || fs.existsSync(destination)) throw new Error("overlay install preflight changed; refusing partial application");
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.copyFileSync(source, destination);
    action.status = "copied";
  }
  const result = { ...plan, status: "OVERLAY_INSTALL_APPLIED", dry_run: false, mutated: true };
  delete result._source_paths;
  return result;
}

export function installPrivateOverlay({ overlayPath, catalogPath, baseManifest, manifestRoot, privateRoot, targetRoot, apply = false, allowHome = false }) {
  const { overlay, catalog } = validatedInputs({ overlayPath, catalogPath, baseManifest, manifestRoot });
  const plan = buildInstallPlan({ overlay, catalog, baseManifest, manifestRoot, privateRoot, targetRoot, apply, allowHome });
  if (apply && plan.status === "OVERLAY_INSTALL_READY") return applyInstallPlan(plan);
  delete plan._source_paths;
  return plan;
}
