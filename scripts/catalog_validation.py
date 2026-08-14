#!/usr/bin/env python3
"""Validate the portable workbench catalog without third-party packages.

Validation is cumulative: schema, taxonomy membership, path custody, local-link
safety, and install mode are independent boundaries and all applicable errors
are reported. A snapshot-only assessment must stay limited to the fields and
file facts supplied by that snapshot; it must not imply a live filesystem read
or introduce an additional identifier rule as observed evidence.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.catalog_entries import entry_type, load_taxonomy  # noqa: E402

MANIFEST_RELATIVE_PATH = Path("catalog/manifest.json")
ALLOWED_ASSET_CLASSES = {"portable", "adapter", "case-study", "external", "excluded"}
ALLOWED_KINDS = {"adapter", "case-study", "cli", "fixture", "reference", "skill", "workflow"}
ALLOWED_MATURITIES = {"experimental", "alpha", "beta", "stable", "reference"}
ALLOWED_TARGETS = {"generic", "codex", "claude", "cursor", "copilot", "gemini", "antigravity"}
ALLOWED_INSTALL_MODES = {"copy", "stage", "manual"}
ALLOWED_PROVENANCE_STATUSES = {"authored", "external-reference", "sanitized-derived"}
ALLOWED_LICENSE_STATUSES = {
    "MIT",
    "MIT-compatible",
    "not-redistributed",
    "reference-only",
}
SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]+$")
PRIVATE_REFERENCE_PATTERN = re.compile(
    r"(?:/(?:Users|home|private)/|~/(?:\.ssh|Library|\.config))"
)
EDITORIAL_TEXT_FIELDS = {"why", "use_when", "avoid_when"}


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
        errors.append(
            f"{path_label}: dependency command must be a simple executable name"
        )
    return errors


def _validate_slug_list(path_label: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        return [f"{path_label}: must be a list"]
    errors: list[str] = []
    if len(value) != len(set(item for item in value if isinstance(item, str))):
        errors.append(f"{path_label}: contains duplicate values")
    for item in value:
        if not isinstance(item, str) or not SOURCE_ID_PATTERN.fullmatch(item):
            errors.append(f"{path_label}: values must be lowercase slugs")
    return errors


def _validate_taxonomy(root: Path, asset_ids: set[str]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    try:
        taxonomy = load_taxonomy(root)
    except ValueError as exc:
        return [str(exc)], {}
    if taxonomy.get("schema_version") != 1:
        errors.append("catalog/taxonomy.json: schema_version must be 1")
    if taxonomy.get("human_name") != "multiplier":
        errors.append("catalog/taxonomy.json: human_name must be multiplier")
    if taxonomy.get("record_name") != "entry":
        errors.append("catalog/taxonomy.json: record_name must be entry")
    if taxonomy.get("physical_layout") != "library/<type>/<slug>/":
        errors.append(
            "catalog/taxonomy.json: physical_layout must be library/<type>/<slug>/"
        )

    types = taxonomy.get("types")
    type_ids: set[str] = set()
    directories: set[str] = set()
    if not isinstance(types, list) or not types:
        errors.append("catalog/taxonomy.json: types must be a non-empty list")
    else:
        for index, item in enumerate(types):
            label = f"catalog/taxonomy.json types[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label}: must be an object")
                continue
            type_id = item.get("id")
            directory = item.get("directory")
            if not isinstance(type_id, str) or not SOURCE_ID_PATTERN.fullmatch(type_id):
                errors.append(f"{label}: id must be a lowercase slug")
            elif type_id in type_ids:
                errors.append(f"{label}: duplicate type id {type_id}")
            else:
                type_ids.add(type_id)
            if not isinstance(directory, str) or not SOURCE_ID_PATTERN.fullmatch(directory):
                errors.append(f"{label}: directory must be a lowercase slug")
            elif directory in directories:
                errors.append(f"{label}: duplicate directory {directory}")
            else:
                directories.add(directory)
            for key in ("label", "purpose"):
                if not isinstance(item.get(key), str) or not item.get(key):
                    errors.append(f"{label}: {key} must be a non-empty string")

    defaults = taxonomy.get("kind_defaults")
    if not isinstance(defaults, dict) or set(defaults) != ALLOWED_KINDS:
        errors.append(
            "catalog/taxonomy.json: kind_defaults must map every supported asset kind"
        )
    elif any(value not in type_ids for value in defaults.values()):
        errors.append("catalog/taxonomy.json: kind_defaults references an unknown type")

    seen_collections: set[str] = set()
    collections = taxonomy.get("collections")
    if not isinstance(collections, list):
        errors.append("catalog/taxonomy.json: collections must be a list")
    else:
        for index, collection in enumerate(collections):
            label = f"catalog/taxonomy.json collections[{index}]"
            if not isinstance(collection, dict):
                errors.append(f"{label}: must be an object")
                continue
            collection_id = collection.get("id")
            if (
                not isinstance(collection_id, str)
                or not SOURCE_ID_PATTERN.fullmatch(collection_id)
            ):
                errors.append(f"{label}: id must be a lowercase slug")
            elif collection_id in seen_collections:
                errors.append(f"{label}: duplicate collection id {collection_id}")
            else:
                seen_collections.add(collection_id)
            for key in ("title", "summary"):
                if not isinstance(collection.get(key), str) or not collection.get(key):
                    errors.append(f"{label}: {key} must be a non-empty string")
            entries = collection.get("entries")
            errors.extend(_validate_slug_list(f"{label} entries", entries))
            if isinstance(entries, list):
                for asset_id in entries:
                    if isinstance(asset_id, str) and asset_id not in asset_ids:
                        errors.append(f"{label}: unknown entry {asset_id}")
    return errors, taxonomy


def _validate_editorial(
    label: str, asset: dict[str, Any], taxonomy: dict[str, Any]
) -> list[str]:
    editorial = asset.get("editorial")
    if editorial is None:
        return []
    if not isinstance(editorial, dict):
        return [f"{label}: editorial must be an object"]
    errors: list[str] = []
    allowed = EDITORIAL_TEXT_FIELDS | {"type", "topics", "use_cases"}
    unknown = set(editorial) - allowed
    if unknown:
        errors.append(f"{label}: unsupported editorial fields {sorted(unknown)}")
    type_ids = {
        item.get("id")
        for item in taxonomy.get("types", [])
        if isinstance(item, dict)
    }
    if "type" in editorial and editorial.get("type") not in type_ids:
        errors.append(f"{label}: editorial type is not in the taxonomy")
    for field in ("topics", "use_cases"):
        if field in editorial:
            errors.extend(
                _validate_slug_list(f"{label} editorial {field}", editorial[field])
            )
    for field in EDITORIAL_TEXT_FIELDS:
        if field in editorial and (
            not isinstance(editorial[field], str) or not editorial[field].strip()
        ):
            errors.append(f"{label}: editorial {field} must be a non-empty string")
    return errors


def _validate_library(root: Path, assets: list[Any], taxonomy: dict[str, Any]) -> list[str]:
    library = root / "library"
    if not library.is_dir():
        return ["library/: missing entry library"]
    by_id = {
        asset.get("id"): asset
        for asset in assets
        if isinstance(asset, dict) and isinstance(asset.get("id"), str)
    }
    directory_types = {
        item["directory"]: item["id"]
        for item in taxonomy.get("types", [])
        if isinstance(item, dict)
        and isinstance(item.get("directory"), str)
        and isinstance(item.get("id"), str)
    }
    errors: list[str] = []
    for type_dir in sorted(path for path in library.iterdir() if path.is_dir()):
        expected_type = directory_types.get(type_dir.name)
        if expected_type is None:
            errors.append(f"library/{type_dir.name}: directory is not in the taxonomy")
            continue
        for entry_dir in sorted(path for path in type_dir.iterdir() if path.is_dir()):
            asset = by_id.get(entry_dir.name)
            if asset is None:
                errors.append(
                    f"library/{type_dir.name}/{entry_dir.name}: missing manifest entry"
                )
            elif entry_type(asset, taxonomy) != expected_type:
                errors.append(
                    f"library/{type_dir.name}/{entry_dir.name}: manifest type does not match directory"
                )
    return errors


def _validate_asset(
    root: Path,
    asset: Any,
    seen_ids: set[str],
    taxonomy: dict[str, Any] | None = None,
    *,
    snapshot: bool = False,
) -> list[str]:
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

    for key in (
        "kind",
        "asset_class",
        "title",
        "summary",
        "maturity",
        "capabilities",
        "supported_targets",
        "entrypoints",
        "files",
        "dependencies",
        "provenance",
        "evidence",
        "install",
    ):
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
    errors.extend(_validate_editorial(label, asset, taxonomy or {}))

    for key in (
        "capabilities",
        "supported_targets",
        "entrypoints",
        "files",
        "dependencies",
        "evidence",
    ):
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
            if not snapshot and not file_path.is_file():
                errors.append(f"{label}: missing file {file_value}")

    entrypoints = asset.get("entrypoints", [])
    if isinstance(entrypoints, list):
        for entrypoint in entrypoints:
            if entrypoint not in files:
                errors.append(
                    f"{label}: entrypoint is not listed in files: {entrypoint}"
                )

    dependencies = asset.get("dependencies", [])
    if isinstance(dependencies, list):
        for index, dependency in enumerate(dependencies):
            errors.extend(
                _validate_dependency(f"{label} dependency {index}", dependency)
            )

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
        errors.extend(
            _validate_source_reference(f"{label} provenance", provenance.get("source"))
        )
        if asset_class == "external" and redistribution != "reference-only":
            errors.append(f"{label}: external assets must be reference-only")
        if asset_class != "external" and redistribution != "allowed":
            errors.append(f"{label}: non-external assets must be redistributable")

    evidence = asset.get("evidence", [])
    if isinstance(evidence, list):
        for evidence_ref in evidence:
            if not isinstance(evidence_ref, str) or not evidence_ref:
                errors.append(f"{label}: evidence references must be strings")
            elif not snapshot and (
                not _is_url(evidence_ref)
                and not (root / evidence_ref.split("#", 1)[0]).is_file()
            ):
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
                errors.append(
                    f"{label}: {mode} install requires a relative destination"
                )
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
                        errors.append(
                            f"{label}: path_map source is not listed in files: {source}"
                        )
                    if not _is_relative_path(target):
                        errors.append(
                            f"{label}: path_map destination must be relative: {target!r}"
                        )

    return errors


def validate_supplied_asset_snapshot(
    asset: Mapping[str, Any], taxonomy_type_ids: Iterable[str]
) -> dict[str, Any]:
    """Validate supplied asset boundaries without reading the filesystem.

    Forward-test callers can use this helper when a manifest entry and
    taxonomy membership are supplied as synthetic evidence. It reports the
    private-source, editorial-type, and installation-mode checks independently
    while keeping filesystem-dependent dimensions explicitly unknown.
    """

    taxonomy_types = {value for value in taxonomy_type_ids if isinstance(value, str)}
    errors: list[str] = []

    provenance = asset.get("provenance")
    source = asset.get("source")
    if isinstance(provenance, Mapping):
        source = provenance.get("source", source)
    private_source = isinstance(source, str) and bool(PRIVATE_REFERENCE_PATTERN.search(source))
    if private_source:
        errors.append("asset source is a private absolute path")

    editorial = asset.get("editorial")
    editorial_type = editorial.get("type") if isinstance(editorial, Mapping) else None
    editorial_supplied = isinstance(editorial_type, str)
    editorial_known = editorial_supplied and editorial_type in taxonomy_types
    if editorial_supplied and not editorial_known:
        errors.append("editorial type is not in the supplied taxonomy")

    install = asset.get("install")
    install_mode = install.get("mode") if isinstance(install, Mapping) else None
    install_supplied = isinstance(install_mode, str)
    install_known = install_supplied and install_mode in ALLOWED_INSTALL_MODES
    if install_supplied and not install_known:
        errors.append(f"installation mode is unsupported: {install_mode!r}")

    return {
        "status": "pass" if not errors else "fail",
        "validation_scope": "supplied-asset-snapshot",
        "errors": errors,
        "checks": {
            "private_source": "fail" if private_source else "pass",
            "editorial_type": (
                "pass" if editorial_known else "fail" if editorial_supplied else "unknown"
            ),
            "installation_mode": (
                "pass" if install_known else "fail" if install_supplied else "unknown"
            ),
        },
        "unknown_checks": [
            "filesystem custody and file existence",
            "evidence existence",
            "library directory completeness and type alignment",
            "local Markdown link resolution",
        ],
    }


def validate_manifest(root: Path, *, snapshot: bool = False) -> list[str]:
    """Return catalog validation errors for a repository root.

    ``snapshot=True`` validates only the supplied manifest/taxonomy shape and
    safe relative-reference syntax. Filesystem-dependent existence, library
    completeness, and local Markdown-link checks are intentionally omitted;
    callers must report those dimensions as unknown rather than treating a
    snapshot-limited pass as a full repository pass.
    """

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
        errors.append(
            "catalog/manifest.json: asset_policy must describe every public asset class"
        )

    source_map = manifest.get("source_map")
    if not isinstance(source_map, list) or not source_map:
        errors.append("catalog/manifest.json: source_map must be a non-empty list")
    else:
        for index, source in enumerate(source_map):
            if not isinstance(source, dict):
                errors.append(f"source_map[{index}]: must be an object")
                continue
            if source.get("class") not in ALLOWED_ASSET_CLASSES:
                errors.append(
                    f"source_map[{index}]: invalid class {source.get('class')!r}"
                )
            errors.extend(
                _validate_source_reference(
                    f"source_map[{index}]", source.get("source_id")
                )
            )
            errors.extend(
                _validate_source_reference(
                    f"source_map[{index}]", source.get("treatment")
                )
            )

    assets = manifest.get("assets")
    asset_ids = (
        {
            asset.get("id")
            for asset in assets
            if isinstance(asset, dict) and isinstance(asset.get("id"), str)
        }
        if isinstance(assets, list)
        else set()
    )
    taxonomy_errors, taxonomy = _validate_taxonomy(root, asset_ids)
    errors.extend(taxonomy_errors)
    if not isinstance(assets, list) or not assets:
        errors.append("catalog/manifest.json: assets must be a non-empty list")
    else:
        seen_ids: set[str] = set()
        for asset in assets:
            errors.extend(
                _validate_asset(root, asset, seen_ids, taxonomy, snapshot=snapshot)
            )
        if not snapshot:
            errors.extend(_validate_library(root, assets, taxonomy))

    if not snapshot:
        for path in sorted(root.rglob("*.md")):
            if any(
                part
                in {".git", ".pre-cr", ".quality-runner", ".aios", ".tmcp", "__pycache__"}
                for part in path.parts
            ):
                continue
            errors.extend(_validate_markdown_links(root, path))
    return errors


def validate_manifest_snapshot(
    root: Path, supplied_evidence: dict[str, bool] | None = None
) -> dict[str, Any]:
    """Return a bounded result that keeps omitted checks explicitly unknown.

    ``supplied_evidence`` is an optional caller-owned snapshot, not a filesystem
    probe.  When it explicitly asserts ``taxonomy_membership``, ``regular_file``,
    or ``no_local_absolute_links``, those dimensions are recorded as passing for
    the supplied snapshot only.  No omitted fact is inferred from the manifest.
    """

    errors = validate_manifest(root, snapshot=True)
    manifest = load_manifest(root)
    taxonomy = load_taxonomy(root)
    assets = manifest.get("assets", [])
    supplied_asset_ids = [
        asset.get("id")
        for asset in assets
        if isinstance(asset, dict) and isinstance(asset.get("id"), str)
    ]
    relative_references = all(
        _is_relative_path(reference)
        for asset in assets
        if isinstance(asset, dict)
        for reference in asset.get("entrypoints", []) + asset.get("files", [])
        if isinstance(reference, str)
    )
    install_modes = sorted(
        {
            str(asset.get("install", {}).get("mode"))
            for asset in assets
            if isinstance(asset, dict) and isinstance(asset.get("install"), dict)
        }
    )
    evidence = supplied_evidence or {}
    snapshot_checks = {
        "taxonomy_membership": "pass"
        if evidence.get("taxonomy_membership") is True
        else "unknown",
        "filesystem_custody": "pass"
        if evidence.get("regular_file") is True
        else "unknown",
        "markdown_links": "pass"
        if evidence.get("no_local_absolute_links") is True
        else "unknown",
    }
    unknown_checks: list[str] = []
    if evidence.get("taxonomy_membership") is not True:
        unknown_checks.append("taxonomy membership, unless explicitly supplied")
    if evidence.get("regular_file") is not True:
        unknown_checks.append(
            "filesystem file and evidence existence, unless explicitly supplied"
        )
    unknown_checks.extend(
        [
            "library directory completeness and type alignment",
            "local Markdown link resolution, unless explicitly supplied",
        ]
    )
    return {
        "status": "pass" if not errors else "fail",
        "validation_scope": "snapshot-limited",
        "errors": errors,
        "checks": {
            "manifest_schema": "pass" if manifest.get("schema_version") == 1 else "fail",
            "taxonomy_schema": "pass" if taxonomy.get("schema_version") == 1 else "fail",
            **snapshot_checks,
            "asset_ids": supplied_asset_ids,
            "relative_references": "pass" if relative_references else "fail",
            "install_modes": install_modes,
        },
        "unknown_checks": unknown_checks,
    }


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
