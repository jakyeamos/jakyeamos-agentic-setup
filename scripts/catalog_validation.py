#!/usr/bin/env python3
"""Validate the portable workbench catalog without third-party packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

MANIFEST_RELATIVE_PATH = Path("catalog/manifest.json")
ALLOWED_ASSET_CLASSES = {"portable", "adapter", "case-study", "external", "excluded"}
ALLOWED_KINDS = {"adapter", "case-study", "fixture", "reference", "skill", "workflow"}
ALLOWED_MATURITIES = {"experimental", "alpha", "beta", "stable", "reference"}
ALLOWED_TARGETS = {"generic", "codex", "claude", "cursor", "copilot", "gemini"}
ALLOWED_INSTALL_MODES = {"copy", "stage", "manual"}
ALLOWED_PROVENANCE_STATUSES = {"authored", "external-reference", "sanitized-derived"}
ALLOWED_LICENSE_STATUSES = {"MIT", "MIT-compatible", "not-redistributed", "reference-only"}
SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]+$")
PRIVATE_REFERENCE_PATTERN = re.compile(
    r"(?:/(?:Users|home|private/var)/|~/(?:\.ssh|Library|\.config))"
)


def load_manifest(root: Path) -> dict[str, Any]:
    """Load the manifest from a repository root."""

    path = root / MANIFEST_RELATIVE_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{path}: missing manifest") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: manifest root must be an object")
    return value


def _is_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _within_root(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _markdown_links(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def _validate_markdown_links(root: Path, path: Path) -> list[str]:
    errors: list[str] = []
    for target in _markdown_links(path.read_text(encoding="utf-8", errors="replace")):
        clean_target = target.split("#", 1)[0].strip()
        if not clean_target or clean_target.startswith("#") or _is_url(clean_target):
            continue
        target_path = (path.parent / clean_target).resolve()
        if not _within_root(root, target_path) or not target_path.exists():
            errors.append(f"{path}: broken local link {target}")
    return errors


def _validate_source_reference(path_label: str, source: Any) -> list[str]:
    if not isinstance(source, str) or not source.strip():
        return [f"{path_label}: provenance source must be a non-empty string"]
    if PRIVATE_REFERENCE_PATTERN.search(source):
        return [f"{path_label}: provenance contains a private path"]
    if "Authorization:" in source or "Bearer " in source:
        return [f"{path_label}: provenance contains a raw authorization reference"]
    return []


def _validate_dependency(path_label: str, dependency: Any) -> list[str]:
    if not isinstance(dependency, dict):
        return [f"{path_label}: dependency must be an object"]
    errors: list[str] = []
    for key in ("name", "kind", "required"):
        if key not in dependency:
            errors.append(f"{path_label}: dependency missing {key}")
    if not isinstance(dependency.get("name"), str) or not dependency.get("name"):
        errors.append(f"{path_label}: dependency name must be a non-empty string")
    if not isinstance(dependency.get("kind"), str) or not dependency.get("kind"):
        errors.append(f"{path_label}: dependency kind must be a non-empty string")
    if not isinstance(dependency.get("required"), bool):
        errors.append(f"{path_label}: dependency required must be boolean")
    command = dependency.get("command")
    if command is not None and (
        not isinstance(command, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", command)
    ):
        errors.append(f"{path_label}: dependency command must be a simple executable name")
    return errors


def _validate_asset(root: Path, asset: Any, seen_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(asset, dict):
        return ["assets: each asset must be an object"]

    asset_id = asset.get("id")
    label = f"asset {asset_id or '<missing-id>'}"
    if not isinstance(asset_id, str) or not SOURCE_ID_PATTERN.fullmatch(asset_id):
        errors.append(f"{label}: id must match {SOURCE_ID_PATTERN.pattern}")
    elif asset_id in seen_ids:
        errors.append(f"asset {asset_id}: duplicate id")
    else:
        seen_ids.add(asset_id)

    for key in ("kind", "asset_class", "title", "summary", "maturity", "capabilities", "supported_targets", "entrypoints", "files", "dependencies", "provenance", "evidence", "install"):
        if key not in asset:
            errors.append(f"{label}: missing {key}")

    kind = asset.get("kind")
    if kind not in ALLOWED_KINDS:
        errors.append(f"{label}: unsupported kind {kind!r}")
    asset_class = asset.get("asset_class")
    if asset_class not in ALLOWED_ASSET_CLASSES:
        errors.append(f"{label}: unsupported asset class {asset_class!r}")
    maturity = asset.get("maturity")
    if maturity not in ALLOWED_MATURITIES:
        errors.append(f"{label}: unsupported maturity {maturity!r}")

    for key in ("capabilities", "supported_targets", "entrypoints", "files", "dependencies", "evidence"):
        if not isinstance(asset.get(key), list):
            errors.append(f"{label}: {key} must be a list")

    targets = asset.get("supported_targets", [])
    if isinstance(targets, list):
        if len(targets) != len(set(targets)):
            errors.append(f"{label}: duplicate supported target")
        for target in targets:
            if target not in ALLOWED_TARGETS:
                errors.append(f"{label}: unsupported target {target!r}")

    files = asset.get("files", [])
    if isinstance(files, list):
        if len(files) != len(set(files)):
            errors.append(f"{label}: duplicate file reference")
        for file_value in files:
            if not _is_relative_path(file_value):
                errors.append(f"{label}: invalid file path {file_value!r}")
                continue
            file_path = root / file_value
            if not file_path.is_file():
                errors.append(f"{label}: missing file {file_value}")

    entrypoints = asset.get("entrypoints", [])
    if isinstance(entrypoints, list):
        for entrypoint in entrypoints:
            if entrypoint not in files:
                errors.append(f"{label}: entrypoint is not listed in files: {entrypoint}")

    dependencies = asset.get("dependencies", [])
    if isinstance(dependencies, list):
        for index, dependency in enumerate(dependencies):
            errors.extend(_validate_dependency(f"{label} dependency {index}", dependency))

    provenance = asset.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{label}: provenance must be an object")
    else:
        status = provenance.get("status")
        license_status = provenance.get("license_status")
        redistribution = provenance.get("redistribution")
        if status not in ALLOWED_PROVENANCE_STATUSES:
            errors.append(f"{label}: invalid provenance status {status!r}")
        if license_status not in ALLOWED_LICENSE_STATUSES:
            errors.append(f"{label}: invalid license status {license_status!r}")
        if redistribution not in {"allowed", "reference-only"}:
            errors.append(f"{label}: invalid redistribution status {redistribution!r}")
        errors.extend(_validate_source_reference(f"{label} provenance", provenance.get("source")))
        if asset_class == "external" and redistribution != "reference-only":
            errors.append(f"{label}: external assets must be reference-only")
        if asset_class != "external" and redistribution != "allowed":
            errors.append(f"{label}: non-external assets must be redistributable")

    evidence = asset.get("evidence", [])
    if isinstance(evidence, list):
        for evidence_ref in evidence:
            if not isinstance(evidence_ref, str) or not evidence_ref:
                errors.append(f"{label}: evidence references must be strings")
            elif not _is_url(evidence_ref) and not (root / evidence_ref.split("#", 1)[0]).is_file():
                errors.append(f"{label}: missing evidence reference {evidence_ref}")

    external_links = asset.get("external_links", [])
    if external_links is not None:
        if not isinstance(external_links, list):
            errors.append(f"{label}: external_links must be a list")
        else:
            for link in external_links:
                if not isinstance(link, str) or not _is_url(link):
                    errors.append(f"{label}: invalid external link {link!r}")

    install = asset.get("install")
    if not isinstance(install, dict):
        errors.append(f"{label}: install must be an object")
    else:
        mode = install.get("mode")
        if mode not in ALLOWED_INSTALL_MODES:
            errors.append(f"{label}: invalid installation mode {mode!r}")
        destination = install.get("destination")
        if mode in {"copy", "stage"}:
            if not _is_relative_path(destination):
                errors.append(f"{label}: {mode} install requires a relative destination")
        if mode == "manual" and not isinstance(install.get("manual_review"), str):
            errors.append(f"{label}: manual install requires manual_review guidance")
        if asset_class == "adapter" and mode != "stage":
            errors.append(f"{label}: adapters must use stage installation")
        if asset_class == "external" and mode != "manual":
            errors.append(f"{label}: external assets must use manual installation")
        path_map = install.get("path_map", {})
        if path_map is not None:
            if not isinstance(path_map, dict):
                errors.append(f"{label}: install path_map must be an object")
            else:
                for source, target in path_map.items():
                    if source not in files:
                        errors.append(f"{label}: path_map source is not listed in files: {source}")
                    if not _is_relative_path(target):
                        errors.append(f"{label}: path_map destination must be relative: {target!r}")

    return errors


def validate_manifest(root: Path) -> list[str]:
    """Return catalog validation errors for a repository root."""

    errors: list[str] = []
    try:
        manifest = load_manifest(root)
    except ValueError as exc:
        return [str(exc)]

    if manifest.get("schema_version") != 1:
        errors.append("catalog/manifest.json: schema_version must be 1")
    workbench = manifest.get("workbench")
    if not isinstance(workbench, dict):
        errors.append("catalog/manifest.json: workbench must be an object")
    else:
        for key in ("id", "name", "repository", "version", "license"):
            if not isinstance(workbench.get(key), str) or not workbench.get(key):
                errors.append(f"catalog/manifest.json: workbench missing {key}")
        if workbench.get("license") != "MIT":
            errors.append("catalog/manifest.json: workbench license must remain MIT")

    policy = manifest.get("asset_policy")
    if not isinstance(policy, dict) or set(ALLOWED_ASSET_CLASSES) - set(policy):
        errors.append("catalog/manifest.json: asset_policy must describe every public asset class")

    source_map = manifest.get("source_map")
    if not isinstance(source_map, list) or not source_map:
        errors.append("catalog/manifest.json: source_map must be a non-empty list")
    else:
        for index, source in enumerate(source_map):
            if not isinstance(source, dict):
                errors.append(f"source_map[{index}]: must be an object")
                continue
            if source.get("class") not in ALLOWED_ASSET_CLASSES:
                errors.append(f"source_map[{index}]: invalid class {source.get('class')!r}")
            errors.extend(_validate_source_reference(f"source_map[{index}]", source.get("source_id")))
            errors.extend(_validate_source_reference(f"source_map[{index}]", source.get("treatment")))

    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        errors.append("catalog/manifest.json: assets must be a non-empty list")
    else:
        seen_ids: set[str] = set()
        for asset in assets:
            errors.extend(_validate_asset(root, asset, seen_ids))

    for path in sorted(root.rglob("*.md")):
        if any(part in {".git", ".pre-cr", ".quality-runner", ".aios", ".tmcp", "__pycache__"} for part in path.parts):
            continue
        errors.extend(_validate_markdown_links(root, path))
    return errors


def main() -> int:
    """Run catalog validation for the checkout containing this script."""

    root = Path(__file__).resolve().parents[1]
    errors = validate_manifest(root)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("catalog validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
