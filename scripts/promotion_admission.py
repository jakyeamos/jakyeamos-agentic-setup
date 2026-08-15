#!/usr/bin/env python3
"""Validate leverage candidates and produce a sanitized JAS admission plan."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, cast
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.catalog_validation import (  # noqa: E402
    _validate_asset,
    load_manifest,
    validate_manifest,
)
from scripts.catalog_entries import load_taxonomy  # noqa: E402

CANDIDATE_SCHEMA_VERSION = "leverage-promotion-candidate/v1"
PROJECTION_SCHEMA_VERSION = "jas-promotion-projection/v1"
PRIVATE_PROJECTION_SCHEMA_VERSION = "jas-promotion-projection/v2"
EDITORIAL_PROJECTION_SCHEMA_VERSION = "jas-promotion-projection/v3"
PUBLIC_PROJECTION_SCHEMA_VERSIONS = {
    PROJECTION_SCHEMA_VERSION,
    EDITORIAL_PROJECTION_SCHEMA_VERSION,
}
APPROVAL_SCHEMA_VERSION = "jas-promotion-approval/v1"
PRIVATE_PACKAGE_SCHEMA_VERSION = "leverage-private-package/v1"
PRIVATE_OVERLAY_SCHEMA_VERSION = "jas-private-overlay/v2"
PUBLIC_SOURCE_ID = "leverage-promotion-candidate"
CANDIDATE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]+$")
OVERLAY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]+$")
PACKAGE_REF_PATTERN = re.compile(r"^artifact:[a-z0-9][a-z0-9:_-]*$")
SYMBOLIC_HOME_PATTERN = re.compile(r"^\$(?:\{HOME\}|HOME)(?:/[A-Za-z0-9._-]+)*$")
_PRIVATE_STRING_PREFIXES = (
    "/" + "Users" + "/",
    "/" + "home" + "/",
    "/" + "private" + "/" + "var" + "/",
    "~" + "/" + ".ssh",
    "~" + "/" + "Library",
    "~" + "/" + ".config",
)
PRIVATE_STRING_PATTERN = re.compile(
    "(?:"
    + "|".join(re.escape(prefix) for prefix in _PRIVATE_STRING_PREFIXES)
    + r"|Authorization:|Bearer )"
)
ASSET_CLASSES = {"portable", "adapter", "case-study", "external", "excluded"}
PUBLIC_ASSET_CLASSES = {"portable", "adapter", "external"}
VISIBILITIES = {"public", "private-overlay"}
PRIVATE_ASSET_KINDS = {
    "skill",
    "workflow",
    "prompt",
    "advice",
    "guardrail",
    "adapter",
    "other",
}
PRIVATE_MATURITIES = {"experimental", "beta", "stable", "reference"}
PRIVATE_TARGETS = {
    "generic",
    "codex",
    "claude",
    "gemini",
    "cursor",
    "antigravity",
    "copilot",
}
PRIVATE_INSTALL_MODES = {"copy", "stage"}


class AdmissionError(ValueError):
    """Raised when a candidate cannot cross the JAS admission boundary."""


def load_json(path: Path) -> dict[str, object]:
    """Load one JSON object without echoing its contents in failures."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdmissionError(f"unable to read JSON input: {path.name}") from exc
    if not isinstance(value, dict):
        raise AdmissionError("JSON input must be an object")
    return cast(dict[str, object], value)


def validate_candidate(candidate: Mapping[str, object]) -> dict[str, object]:
    """Validate the leverage candidate without exposing its private evidence."""

    _required_exact(candidate, "schema_version", CANDIDATE_SCHEMA_VERSION)
    preflight_errors: list[str] = []
    if _private_value_present(candidate):
        preflight_errors.append(
            "candidate contains a private absolute path or credential-shaped value"
        )
    if candidate.get("status") != "candidate":
        preflight_errors.append("candidate must remain in candidate status for JAS admission")
    if preflight_errors:
        raise AdmissionError("; ".join(preflight_errors))
    _required_exact(candidate, "visibility", "private")
    candidate_id = _required_text(candidate, "candidate_id")
    if not CANDIDATE_ID_PATTERN.fullmatch(candidate_id):
        raise AdmissionError("candidate_id must be a safe identifier")
    _required_text(candidate, "title")
    asset_kind = _required_enum(
        candidate,
        "asset_kind",
        {
            "skill",
            "workflow",
            "prompt",
            "advice",
            "guardrail",
            "adapter",
            "reference",
            "other",
        },
    )
    _required_string_list(candidate, "source_refs")
    _required_text(candidate, "trigger")
    _required_text(candidate, "non_trigger")
    _required_text(candidate, "expected_behavior")
    for field in (
        "input_contract",
        "output_contract",
        "decision_path",
        "safety_boundary",
        "verifier",
    ):
        _required_string_list(candidate, field)
    _required_text(candidate, "stopping_condition")
    _required_text(candidate, "clean_room_fixture_ref")
    _required_string_list(candidate, "evidence_refs")
    quantification = candidate.get("quantification")
    if not isinstance(quantification, dict) or not quantification:
        raise AdmissionError("candidate quantification must be a non-empty object")
    portability = _required_enum(
        candidate,
        "portability",
        {"portable", "reference-only", "private", "excluded", "unknown"},
    )
    if portability == "portable":
        _required_string_list(candidate, "portable_artifact_refs")
    _required_string_list(candidate, "redaction_notes")
    status = _required_enum(
        candidate,
        "status",
        {
            "candidate",
            "reviewed",
            "promoted",
            "staged",
            "installed",
            "verified",
            "deferred",
            "excluded",
        },
    )
    review_status = _required_enum(
        candidate, "review_status", {"pending", "approved", "rejected", "deferred"}
    )
    maturity = _required_enum(
        candidate, "maturity", {"experimental", "beta", "stable", "reference"}
    )
    private_package = _validate_private_package(candidate.get("private_package"), candidate_id)
    promotion_projection = candidate.get("promotion_projection")
    if promotion_projection is not None and not isinstance(promotion_projection, Mapping):
        raise AdmissionError("promotion_projection must be an object")
    if portability == "private" and private_package is None:
        raise AdmissionError("private candidate requires private_package")
    if portability != "private" and private_package is not None:
        raise AdmissionError("private_package is only valid for private candidates")
    if portability == "private":
        _required_text(candidate, "disposition_reason")
    if review_status not in {"pending", "approved"}:
        raise AdmissionError("candidate review_status must be pending or approved")
    return {
        "candidate_id": candidate_id,
        "asset_kind": asset_kind,
        "portability": portability,
        "review_status": review_status,
        "maturity": maturity,
        "private_package": private_package,
        "promotion_projection": (
            None
            if promotion_projection is None
            else dict(cast(Mapping[str, object], promotion_projection))
        ),
    }


def validate_projection(
    projection: Mapping[str, object],
    root: Path,
    candidate_id: str,
    candidate_result: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Validate a human-authored public or private-overlay projection."""

    schema_version = _required_text(projection, "schema_version")
    if schema_version == PRIVATE_PROJECTION_SCHEMA_VERSION:
        visibility = _required_exact(projection, "visibility", "private-overlay")
        if _required_text(projection, "candidate_id") != candidate_id:
            raise AdmissionError("projection candidate_id does not match candidate")
        private_package = None if candidate_result is None else candidate_result.get("private_package")
        if not isinstance(private_package, Mapping):
            raise AdmissionError("private-overlay projection requires a private candidate package")
        private_asset = _validate_private_asset(
            projection.get("private_asset"),
            candidate_id,
            candidate_result,
            private_package,
        )
        if _private_value_present(projection):
            raise AdmissionError("projection contains a private or credential-shaped value")
        return {
            "schema_version": schema_version,
            "visibility": visibility,
            "asset_id": str(private_asset["id"]),
            "private_asset": private_asset,
        }
    if schema_version not in PUBLIC_PROJECTION_SCHEMA_VERSIONS:
        raise AdmissionError("projection schema_version is unsupported")
    visibility = _required_enum(projection, "visibility", VISIBILITIES)
    if schema_version == EDITORIAL_PROJECTION_SCHEMA_VERSION and visibility != "public":
        raise AdmissionError("v3 public projection requires public visibility")
    if _required_text(projection, "candidate_id") != candidate_id:
        raise AdmissionError("projection candidate_id does not match candidate")
    asset = projection.get("asset")
    if not isinstance(asset, dict):
        raise AdmissionError("projection asset must be an object")
    asset = cast(dict[str, Any], asset)
    asset_id = asset.get("id")
    if not isinstance(asset_id, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]+", asset_id
    ):
        raise AdmissionError("projection asset id is invalid")
    asset_class = asset.get("asset_class")
    if asset_class not in ASSET_CLASSES:
        raise AdmissionError("projection asset class is invalid")
    if visibility == "public" and asset_class not in PUBLIC_ASSET_CLASSES:
        raise AdmissionError(
            "public projection must use a portable, adapter, or external asset class"
        )
    if visibility == "public" and candidate_result is not None:
        portability = candidate_result.get("portability")
        if asset_class == "external" and portability != "reference-only":
            raise AdmissionError(
                "external public projection requires a reference-only candidate"
            )
        if portability == "reference-only" and asset_class != "external":
            raise AdmissionError(
                "reference-only candidate requires an external public projection"
            )
    if visibility == "public" and asset_class == "external":
        external_links = asset.get("external_links")
        if (
            not isinstance(external_links, list)
            or not external_links
            or not all(
                isinstance(link, str)
                and urlparse(link).scheme in {"http", "https"}
                and bool(urlparse(link).netloc)
                for link in external_links
            )
        ):
            raise AdmissionError(
                "external public projection requires at least one public URL"
            )
    private_values = _private_value_present(projection)
    if private_values:
        raise AdmissionError("projection contains a private or credential-shaped value")
    try:
        taxonomy = load_taxonomy(root)
    except ValueError as exc:
        raise AdmissionError("unable to load the JAS catalog taxonomy") from exc
    errors = _validate_asset(root, asset, set(), taxonomy)
    if errors:
        raise AdmissionError("projection asset fails the JAS catalog contract")
    if schema_version == EDITORIAL_PROJECTION_SCHEMA_VERSION:
        _validate_complete_editorial(asset)
    return {
        "schema_version": schema_version,
        "visibility": visibility,
        "asset_id": asset_id,
        "asset": asset,
    }


def _validate_complete_editorial(asset: Mapping[str, object]) -> None:
    """Require the browse metadata expected from new public promotions."""

    editorial = asset.get("editorial")
    if not isinstance(editorial, Mapping):
        raise AdmissionError("v3 public projection requires complete editorial metadata")
    required = {"type", "topics", "use_cases", "why", "use_when", "avoid_when"}
    if set(editorial) != required:
        raise AdmissionError("v3 public projection requires complete editorial metadata")
    for field in ("topics", "use_cases"):
        value = editorial.get(field)
        if not isinstance(value, list) or not value:
            raise AdmissionError(
                f"v3 public projection editorial {field} must be a non-empty list"
            )


def validate_approval(
    approval: Mapping[str, object], candidate_id: str
) -> dict[str, object]:
    """Validate the explicit human approval needed for admission planning."""

    _required_exact(approval, "schema_version", APPROVAL_SCHEMA_VERSION)
    if _required_text(approval, "candidate_id") != candidate_id:
        raise AdmissionError("approval candidate_id does not match candidate")
    if _required_exact(approval, "decision", "approve") != "approve":
        raise AdmissionError("approval decision must be approve")
    _required_text(approval, "reviewer")
    _required_text(approval, "reviewed_at")
    return {
        "reviewer": str(approval["reviewer"]),
        "reviewed_at": str(approval["reviewed_at"]),
    }


def build_plan(
    root: Path,
    candidate: Mapping[str, object],
    projection: Mapping[str, object],
    approval: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build a plan that contains only sanitized projection data."""

    candidate_result = validate_candidate(candidate)
    candidate_id = str(candidate_result["candidate_id"])
    projection_result = validate_projection(projection, root, candidate_id, candidate_result)
    visibility = str(projection_result["visibility"])
    if visibility == "private-overlay":
        if projection_result["schema_version"] == PROJECTION_SCHEMA_VERSION:
            return {
                "schema_version": PROJECTION_SCHEMA_VERSION,
                "status": "blocked",
                "reason": "private_overlay_requires_catalog_asset_reference",
                "candidate_id": candidate_id,
                "asset_id": projection_result["asset_id"],
                "mutated": False,
            }
        if approval is None:
            status = "review_required"
            approval_result: dict[str, object] = {}
        else:
            approval_result = validate_approval(approval, candidate_id)
            status = "ready_for_overlay_review"
        private_asset = cast(dict[str, object], projection_result["private_asset"])
        return {
            "schema_version": PRIVATE_PROJECTION_SCHEMA_VERSION,
            "status": status,
            "candidate_id": candidate_id,
            "asset_id": str(private_asset["id"]),
            "target": "private-overlay.json",
            "source_map_entry": {
                "source_id": PUBLIC_SOURCE_ID,
                "class": "private-overlay",
                "treatment": "sanitized private package metadata only; source and evidence remain outside distribution",
            },
            "asset": private_asset,
            "overlay": _private_overlay(root, candidate_id, private_asset),
            "approval": approval_result,
            "mutated": False,
        }
    if approval is None:
        status = "review_required"
        approval_result: dict[str, object] = {}
    else:
        approval_result = validate_approval(approval, candidate_id)
        status = "ready_for_manifest_review"
    return {
        "schema_version": projection_result["schema_version"],
        "status": status,
        "candidate_id": candidate_id,
        "asset_id": projection_result["asset_id"],
        "target": "catalog/manifest.json",
        "source_map_entry": {
            "source_id": PUBLIC_SOURCE_ID,
            "class": str(
                cast(dict[str, object], projection_result["asset"])["asset_class"]
            ),
            "treatment": "sanitized projection only; private candidate evidence remains outside distribution",
        },
        "asset": projection_result["asset"],
        "approval": approval_result,
        "mutated": False,
    }


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _atomic_write_json(path: Path, value: Mapping[str, object]) -> None:
    _atomic_write_bytes(
        path,
        (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
    )


def _public_manifest_plan(
    root: Path, asset: Mapping[str, object]
) -> dict[str, object]:
    """Prepare a public catalog mutation without touching the manifest."""

    manifest_path = root / "catalog" / "manifest.json"
    current = load_manifest(root)
    existing_errors = validate_manifest(root)
    if existing_errors:
        raise AdmissionError("the current JAS catalog fails validation")
    raw_assets = current.get("assets")
    if not isinstance(raw_assets, list):
        raise AdmissionError("the JAS catalog assets collection is invalid")
    asset_id = _required_text(asset, "id")
    existing = next(
        (item for item in raw_assets if isinstance(item, Mapping) and item.get("id") == asset_id),
        None,
    )
    if existing is not None and _canonical(existing) != _canonical(asset):
        raise AdmissionError("the JAS catalog already contains a conflicting asset id")

    source_map = current.get("source_map")
    if not isinstance(source_map, list):
        raise AdmissionError("the JAS catalog source_map collection is invalid")
    expected_class = _required_text(asset, "asset_class")
    matching_source = next(
        (
            item
            for item in source_map
            if isinstance(item, Mapping) and item.get("source_id") == PUBLIC_SOURCE_ID
        ),
        None,
    )
    if matching_source is not None and matching_source.get("class") != expected_class:
        raise AdmissionError("the JAS promotion source_map entry has a conflicting class")

    candidate_manifest = json.loads(json.dumps(current))
    candidate_assets = [
        dict(item) for item in raw_assets if isinstance(item, Mapping)
    ]
    if existing is None:
        candidate_assets.append(dict(asset))
    candidate_assets.sort(key=lambda item: str(item.get("id", "")))
    candidate_manifest["assets"] = candidate_assets
    candidate_source_map = [
        dict(item) for item in source_map if isinstance(item, Mapping)
    ]
    if matching_source is None:
        candidate_source_map.append(
            {
                "class": expected_class,
                "source_id": PUBLIC_SOURCE_ID,
                "treatment": "sanitized projection only; private candidate evidence remains outside distribution",
            }
        )
        candidate_source_map.sort(key=lambda item: str(item.get("source_id", "")))
    candidate_manifest["source_map"] = candidate_source_map
    return {
        "path": manifest_path,
        "original": manifest_path.read_bytes(),
        "manifest": candidate_manifest,
        "changed": _canonical(candidate_manifest) != _canonical(current),
        "asset_id": asset_id,
    }


def _commit_public_manifest(plan: Mapping[str, object]) -> bool:
    if not bool(plan["changed"]):
        return False
    path = cast(Path, plan["path"])
    _atomic_write_json(path, cast(Mapping[str, object], plan["manifest"]))
    errors = validate_manifest(path.parents[1])
    if errors:
        _atomic_write_bytes(path, cast(bytes, plan["original"]))
        raise AdmissionError("post-apply catalog validation failed")
    return True


def _restore_public_manifest(plan: Mapping[str, object]) -> None:
    _atomic_write_bytes(cast(Path, plan["path"]), cast(bytes, plan["original"]))


def _node_path() -> str:
    node = shutil.which("node")
    if node is None:
        raise AdmissionError("the Node runtime is required for JAS overlay installation")
    return node


def _node_json(root: Path, arguments: list[str]) -> dict[str, object]:
    command = [_node_path(), str(root / "bin" / "agent-config.mjs"), *arguments, "--json"]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AdmissionError("the JAS overlay command could not complete") from exc
    raw = completed.stdout.strip() or completed.stderr.strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdmissionError("the JAS overlay command returned a non-JSON result") from exc
    if not isinstance(value, dict):
        raise AdmissionError("the JAS overlay command returned an invalid result")
    return cast(dict[str, object], value)


def _node_manifest_args(root: Path, catalog: Path | None = None) -> list[str]:
    arguments = ["--catalog", str(catalog or (root / "catalog" / "manifest.json"))]
    manifest_path = root / "manifest.yaml"
    if manifest_path.is_file():
        arguments.extend(["--manifest", str(manifest_path)])
    return arguments


def _validate_overlay_file(
    root: Path, overlay_path: Path, *, catalog: Path | None = None
) -> dict[str, object]:
    result = _node_json(
        root,
        ["overlay", "--overlay", str(overlay_path), *_node_manifest_args(root, catalog)],
    )
    if result.get("status") != "OVERLAY_VALID":
        raise AdmissionError("the merged private overlay fails JAS validation")
    return result


def _overlay_install(
    root: Path,
    overlay_path: Path,
    *,
    private_root: Path | None,
    target_root: Path,
    catalog: Path | None = None,
    apply: bool,
) -> dict[str, object]:
    arguments = [
        "overlay-install",
        "--overlay",
        str(overlay_path),
        "--root",
        str(target_root),
        *_node_manifest_args(root, catalog),
    ]
    if private_root is not None:
        arguments.extend(["--private-root", str(private_root)])
    home = Path.home().resolve()
    if target_root.expanduser().resolve() == home:
        arguments.append("--allow-home")
    arguments.append("--apply" if apply else "--dry-run")
    return _node_json(root, arguments)


def _temporary_json(parent: Path, value: Mapping[str, object]) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", dir=parent, prefix=".jas-promotion-", suffix=".json", delete=False
    )
    temporary = Path(handle.name)
    try:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    return temporary


def _merge_overlay(
    overlay_path: Path, generated: Mapping[str, object]
) -> tuple[dict[str, object], bool]:
    if not overlay_path.exists():
        return dict(generated), True
    if overlay_path.is_symlink() or not overlay_path.is_file():
        raise AdmissionError("the existing private overlay is not a regular file")
    existing = load_json(overlay_path)
    if existing.get("visibility") != "private-overlay":
        raise AdmissionError("the existing private overlay has an unsupported visibility")
    if existing.get("base_workbench_id") != generated.get("base_workbench_id"):
        raise AdmissionError("the existing private overlay targets a different JAS workbench")
    references = existing.get("references")
    generated_references = generated.get("references")
    if not isinstance(references, list) or not isinstance(generated_references, list):
        raise AdmissionError("private overlay references are invalid")
    merged = dict(existing)
    merged_references = [dict(item) for item in references if isinstance(item, Mapping)]
    existing_by_id = {str(item.get("id")): item for item in merged_references}
    for raw_reference in generated_references:
        if not isinstance(raw_reference, Mapping):
            raise AdmissionError("generated private overlay reference is invalid")
        reference = dict(raw_reference)
        reference_id = str(reference.get("id"))
        prior = existing_by_id.get(reference_id)
        if prior is not None:
            if _canonical(prior) != _canonical(reference):
                raise AdmissionError("the private overlay contains a conflicting reference")
            continue
        merged_references.append(reference)
        existing_by_id[reference_id] = reference
    merged_references.sort(key=lambda item: str(item.get("id", "")))
    merged["references"] = merged_references

    generated_assets = generated.get("private_assets")
    if generated_assets is not None:
        prior_assets = merged.get("private_assets", [])
        if not isinstance(prior_assets, list) or not isinstance(generated_assets, list):
            raise AdmissionError("private overlay assets are invalid")
        merged_assets = [dict(item) for item in prior_assets if isinstance(item, Mapping)]
        assets_by_id = {str(item.get("id")): item for item in merged_assets}
        for raw_asset in generated_assets:
            if not isinstance(raw_asset, Mapping):
                raise AdmissionError("generated private overlay asset is invalid")
            asset = dict(raw_asset)
            asset_id = str(asset.get("id"))
            prior = assets_by_id.get(asset_id)
            if prior is not None:
                if _canonical(prior) != _canonical(asset):
                    raise AdmissionError("the private overlay contains a conflicting asset")
                continue
            merged_assets.append(asset)
            assets_by_id[asset_id] = asset
        merged_assets.sort(key=lambda item: str(item.get("id", "")))
        merged["private_assets"] = merged_assets
        merged["schema_version"] = PRIVATE_OVERLAY_SCHEMA_VERSION
    return merged, _canonical(existing) != _canonical(merged)


def _all_actions_exist(result: Mapping[str, object]) -> bool:
    actions = result.get("actions")
    return (
        isinstance(actions, list)
        and bool(actions)
        and all(
            isinstance(action, Mapping) and action.get("status") == "exists"
            for action in actions
        )
    )


def _remove_copied_actions(result: Mapping[str, object]) -> None:
    actions = result.get("actions")
    if not isinstance(actions, list):
        return
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        destination = action.get("destination")
        if isinstance(destination, str):
            path = Path(destination)
            if path.is_file() and not path.is_symlink():
                try:
                    path.unlink()
                except OSError:
                    pass


def _projection_from_candidate(
    candidate: Mapping[str, object], projection_path: Path | None
) -> dict[str, object]:
    if projection_path is not None:
        return load_json(projection_path)
    projection = candidate.get("promotion_projection")
    if not isinstance(projection, Mapping):
        raise AdmissionError(
            "candidate has no embedded sanitized promotion projection; prepare one before approval"
        )
    return dict(cast(Mapping[str, object], projection))


def _public_overlay(
    root: Path, candidate_id: str, asset: Mapping[str, object]
) -> dict[str, object]:
    try:
        manifest = load_manifest(root)
        workbench = manifest.get("workbench")
        workbench_id = workbench.get("id") if isinstance(workbench, Mapping) else None
    except (OSError, ValueError):
        workbench_id = None
    if not isinstance(workbench_id, str) or not OVERLAY_ID_PATTERN.fullmatch(workbench_id):
        workbench_id = "portable-agentic-workbench"
    asset_id = _required_text(asset, "id")
    targets = _target_list(asset, "supported_targets")
    return {
        "schema_version": "jas-private-overlay/v1",
        "visibility": "private-overlay",
        "overlay_id": f"{_overlay_asset_id(candidate_id)}-overlay",
        "base_workbench_id": workbench_id,
        "references": [
            {
                "id": f"{asset_id}-selection",
                "asset_id": asset_id,
                "enabled": True,
                "targets": targets,
            }
        ],
    }


def _apply_private_admission(
    root: Path,
    candidate_id: str,
    private_asset: Mapping[str, object],
    *,
    overlay_path: Path | None,
    private_root: Path | None,
    target_root: Path | None,
) -> dict[str, object]:
    if overlay_path is None or private_root is None or target_root is None:
        raise AdmissionError(
            "private admission requires --overlay-path, --private-root, and --target-root"
        )
    if not private_root.is_dir():
        raise AdmissionError("the private package root is not an existing directory")
    merged, overlay_changed = _merge_overlay(
        overlay_path, _private_overlay(root, candidate_id, private_asset)
    )
    temporary_overlay = _temporary_json(overlay_path.parent, merged)
    try:
        _validate_overlay_file(root, temporary_overlay)
        preflight = _overlay_install(
            root,
            temporary_overlay,
            private_root=private_root,
            target_root=target_root,
            apply=False,
        )
        if preflight.get("status") == "OVERLAY_INSTALL_BLOCKED":
            if not _all_actions_exist(preflight):
                raise AdmissionError("private overlay installation preflight is blocked")
            if overlay_changed:
                _atomic_write_json(overlay_path, merged)
            return {
                "status": "JAS_ALREADY_APPLIED",
                "candidate_id": candidate_id,
                "target": "private-overlay.json",
                "mutated": overlay_changed,
                "install_status": "already_present",
            }
        applied = _overlay_install(
            root,
            temporary_overlay,
            private_root=private_root,
            target_root=target_root,
            apply=True,
        )
        if applied.get("status") != "OVERLAY_INSTALL_APPLIED":
            raise AdmissionError("private overlay installation did not apply")
        try:
            os.replace(temporary_overlay, overlay_path)
        except OSError as exc:
            _remove_copied_actions(applied)
            raise AdmissionError("private overlay receipt could not be committed") from exc
        return {
            "status": "JAS_APPLIED",
            "candidate_id": candidate_id,
            "target": "private-overlay.json",
            "mutated": True,
            "install_status": "applied",
        }
    finally:
        if temporary_overlay.exists():
            temporary_overlay.unlink()


def _apply_public_admission(
    root: Path, candidate_id: str, asset: Mapping[str, object]
) -> dict[str, object]:
    plan = _public_manifest_plan(root, asset)
    changed = _commit_public_manifest(plan)
    return {
        "status": "JAS_APPLIED" if changed else "JAS_ALREADY_APPLIED",
        "candidate_id": candidate_id,
        "target": "catalog/manifest.json",
        "mutated": changed,
        "install_status": "catalog_updated" if changed else "already_present",
    }


def _apply_both_admission(
    root: Path,
    candidate_id: str,
    asset: Mapping[str, object],
    *,
    overlay_path: Path | None,
    target_root: Path | None,
) -> dict[str, object]:
    if overlay_path is None or target_root is None:
        raise AdmissionError("both admission requires --overlay-path and --target-root")
    plan = _public_manifest_plan(root, asset)
    merged, overlay_changed = _merge_overlay(
        overlay_path, _public_overlay(root, candidate_id, asset)
    )
    temporary_overlay = _temporary_json(overlay_path.parent, merged)
    temporary_catalog = _temporary_json(
        root / "catalog", cast(Mapping[str, object], plan["manifest"])
    )
    manifest_committed = False
    try:
        _validate_overlay_file(root, temporary_overlay, catalog=temporary_catalog)
        preflight = _overlay_install(
            root,
            temporary_overlay,
            private_root=None,
            target_root=target_root,
            catalog=temporary_catalog,
            apply=False,
        )
        already_installed = preflight.get("status") == "OVERLAY_INSTALL_BLOCKED" and _all_actions_exist(
            preflight
        )
        if preflight.get("status") == "OVERLAY_INSTALL_BLOCKED" and not already_installed:
            raise AdmissionError("combined JAS admission preflight is blocked")
        manifest_committed = _commit_public_manifest(plan)
        if already_installed:
            if overlay_changed:
                _atomic_write_json(overlay_path, merged)
            return {
                "status": "JAS_ALREADY_APPLIED",
                "candidate_id": candidate_id,
                "target": "catalog/manifest.json + private-overlay.json",
                "mutated": manifest_committed or overlay_changed,
                "install_status": "already_present",
            }
        applied = _overlay_install(
            root,
            temporary_overlay,
            private_root=None,
            target_root=target_root,
            apply=True,
        )
        if applied.get("status") != "OVERLAY_INSTALL_APPLIED":
            raise AdmissionError("combined JAS installation did not apply")
        try:
            os.replace(temporary_overlay, overlay_path)
        except OSError as exc:
            _remove_copied_actions(applied)
            raise AdmissionError("combined JAS receipt could not be committed") from exc
        return {
            "status": "JAS_APPLIED",
            "candidate_id": candidate_id,
            "target": "catalog/manifest.json + private-overlay.json",
            "mutated": True,
            "install_status": "catalog_and_overlay_applied",
        }
    except Exception:
        if manifest_committed:
            _restore_public_manifest(plan)
        raise
    finally:
        if temporary_overlay.exists():
            temporary_overlay.unlink()
        if temporary_catalog.exists():
            temporary_catalog.unlink()


def apply_admission(
    root: Path,
    candidate: Mapping[str, object],
    projection: Mapping[str, object],
    approval: Mapping[str, object],
    *,
    mode: str,
    apply: bool,
    overlay_path: Path | None,
    private_root: Path | None,
    target_root: Path | None,
) -> dict[str, object]:
    """Apply one explicitly approved projection through the JAS mutation boundary."""

    candidate_result = validate_candidate(candidate)
    candidate_id = str(candidate_result["candidate_id"])
    projection_result = validate_projection(
        projection, root, candidate_id, candidate_result
    )
    validate_approval(approval, candidate_id)
    if not apply:
        return {
            "status": "blocked",
            "reason": "apply_requires_explicit_flag",
            "candidate_id": candidate_id,
            "mutated": False,
        }
    visibility = str(projection_result["visibility"])
    if mode in {"public", "both"}:
        if visibility != "public":
            raise AdmissionError(f"{mode} admission requires a public projection")
        portability = candidate_result.get("portability")
        if mode == "public":
            if portability not in {"portable", "reference-only"}:
                raise AdmissionError(
                    "public admission requires a portable or reference-only candidate"
                )
        elif portability != "portable":
            raise AdmissionError("both admission requires a portable candidate")
        asset = cast(dict[str, object], projection_result["asset"])
        if mode == "public":
            return _apply_public_admission(root, candidate_id, asset)
        return _apply_both_admission(
            root,
            candidate_id,
            asset,
            overlay_path=overlay_path,
            target_root=target_root,
        )
    if visibility != "private-overlay" or projection_result["schema_version"] != PRIVATE_PROJECTION_SCHEMA_VERSION:
        raise AdmissionError("private admission requires a v2 private-overlay projection")
    if candidate_result.get("portability") != "private":
        raise AdmissionError("private admission requires a private candidate package")
    return _apply_private_admission(
        root,
        candidate_id,
        cast(dict[str, object], projection_result["private_asset"]),
        overlay_path=overlay_path,
        private_root=private_root,
        target_root=target_root,
    )


def _validate_private_package(
    value: object, candidate_id: str
) -> dict[str, object] | None:
    """Validate the leverage-side package descriptor without accepting host paths."""

    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise AdmissionError("private_package must be an object")
    package = cast(Mapping[str, object], value)
    _reject_unknown(
        package,
        {
            "schema_version",
            "package_id",
            "package_ref",
            "files",
            "entrypoints",
            "redaction_status",
            "redaction_notes",
        },
        "private_package",
    )
    _required_exact(package, "schema_version", PRIVATE_PACKAGE_SCHEMA_VERSION)
    package_id = _required_text(package, "package_id")
    if not CANDIDATE_ID_PATTERN.fullmatch(package_id) or package_id != candidate_id:
        raise AdmissionError("private_package.package_id must match candidate_id")
    package_ref = _required_text(package, "package_ref")
    if not PACKAGE_REF_PATTERN.fullmatch(package_ref):
        raise AdmissionError("private_package.package_ref must be a sanitized artifact reference")
    files = _relative_string_list(package, "files", "private_package.files")
    entrypoints = _relative_string_list(package, "entrypoints", "private_package.entrypoints")
    if any(entrypoint not in files for entrypoint in entrypoints):
        raise AdmissionError("private_package.entrypoints must be listed in private_package.files")
    _required_exact(package, "redaction_status", "sanitized")
    redaction_notes = _required_string_list(package, "redaction_notes")
    return {
        "schema_version": PRIVATE_PACKAGE_SCHEMA_VERSION,
        "package_id": package_id,
        "package_ref": package_ref,
        "files": files,
        "entrypoints": entrypoints,
        "redaction_status": "sanitized",
        "redaction_notes": redaction_notes,
    }


def _validate_private_asset(
    value: object,
    candidate_id: str,
    candidate_result: Mapping[str, object] | None,
    private_package: Mapping[str, object],
) -> dict[str, object]:
    """Validate the sanitized v2 asset that can be placed in a private overlay."""

    if not isinstance(value, Mapping):
        raise AdmissionError("private_asset must be an object")
    asset = cast(Mapping[str, object], value)
    _reject_unknown(
        asset,
        {
            "id",
            "kind",
            "title",
            "summary",
            "maturity",
            "supported_targets",
            "package_ref",
            "package_dir",
            "entrypoints",
            "files",
            "install",
        },
        "private_asset",
    )
    asset_id = _required_text(asset, "id")
    expected_asset_id = _overlay_asset_id(candidate_id)
    if not OVERLAY_ID_PATTERN.fullmatch(asset_id) or asset_id != expected_asset_id:
        raise AdmissionError("private_asset.id must be the normalized candidate identifier")
    kind = _required_enum(asset, "kind", PRIVATE_ASSET_KINDS)
    if candidate_result is not None and kind != candidate_result.get("asset_kind"):
        raise AdmissionError("private_asset.kind does not match candidate")
    title = _required_text(asset, "title")
    summary = _required_text(asset, "summary")
    maturity = _required_enum(asset, "maturity", PRIVATE_MATURITIES)
    if candidate_result is not None and maturity != candidate_result.get("maturity"):
        raise AdmissionError("private_asset.maturity does not match candidate")
    supported_targets = _target_list(asset, "supported_targets")
    package_ref = _required_text(asset, "package_ref")
    if not PACKAGE_REF_PATTERN.fullmatch(package_ref):
        raise AdmissionError("private_asset.package_ref must be a sanitized artifact reference")
    if package_ref != private_package.get("package_ref"):
        raise AdmissionError("private_asset.package_ref does not match candidate package")
    package_dir = _relative_path(asset, "package_dir")
    files = _relative_string_list(asset, "files", "private_asset.files")
    entrypoints = _relative_string_list(asset, "entrypoints", "private_asset.entrypoints")
    if files != list(private_package.get("files", [])):
        raise AdmissionError("private_asset.files do not match candidate package")
    if entrypoints != list(private_package.get("entrypoints", [])):
        raise AdmissionError("private_asset.entrypoints do not match candidate package")
    if any(entrypoint not in files for entrypoint in entrypoints):
        raise AdmissionError("private_asset.entrypoints must be listed in private_asset.files")
    install = asset.get("install")
    if not isinstance(install, Mapping):
        raise AdmissionError("private_asset.install must be an object")
    _reject_unknown(install, {"mode", "destination"}, "private_asset.install")
    mode = _required_enum(install, "mode", PRIVATE_INSTALL_MODES)
    destination = _required_text(install, "destination")
    if not SYMBOLIC_HOME_PATTERN.fullmatch(destination):
        raise AdmissionError("private_asset.install.destination must be anchored to $HOME")
    return {
        "id": asset_id,
        "kind": kind,
        "title": title,
        "summary": summary,
        "maturity": maturity,
        "supported_targets": supported_targets,
        "package_ref": package_ref,
        "package_dir": package_dir,
        "entrypoints": entrypoints,
        "files": files,
        "install": {"mode": mode, "destination": destination},
    }


def _private_overlay(root: Path, candidate_id: str, asset: Mapping[str, object]) -> dict[str, object]:
    """Build an installable v2 overlay using only sanitized projection metadata."""

    try:
        manifest = load_manifest(root)
        workbench = manifest.get("workbench")
        workbench_id = workbench.get("id") if isinstance(workbench, Mapping) else None
    except (OSError, ValueError):
        workbench_id = None
    if not isinstance(workbench_id, str) or not OVERLAY_ID_PATTERN.fullmatch(workbench_id):
        workbench_id = "portable-agentic-workbench"
    asset_id = str(asset["id"])
    targets = list(cast(list[str], asset["supported_targets"]))
    install = cast(dict[str, object], asset["install"])
    return {
        "schema_version": "jas-private-overlay/v2",
        "visibility": "private-overlay",
        "overlay_id": f"{_overlay_asset_id(candidate_id)}-overlay",
        "base_workbench_id": workbench_id,
        "references": [
            {
                "id": f"{asset_id}-selection",
                "asset_id": asset_id,
                "enabled": True,
                "targets": targets,
                "destination": install["destination"],
            }
        ],
        "private_assets": [dict(asset)],
    }


def _overlay_asset_id(candidate_id: str) -> str:
    return candidate_id.replace("_", "-")


def _required_text(document: Mapping[str, object], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value.strip():
        raise AdmissionError(f"{field} must be a non-empty string")
    return value.strip()


def _required_exact(document: Mapping[str, object], field: str, expected: str) -> str:
    value = _required_text(document, field)
    if value != expected:
        raise AdmissionError(f"{field} is not compatible with this admission boundary")
    return value


def _required_enum(
    document: Mapping[str, object], field: str, allowed: set[str]
) -> str:
    value = _required_text(document, field)
    if value not in allowed:
        raise AdmissionError(f"{field} has an unsupported value")
    return value


def _required_string_list(document: Mapping[str, object], field: str) -> list[str]:
    value = document.get(field)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise AdmissionError(f"{field} must contain at least one string")
    return [str(item).strip() for item in value]


def _reject_unknown(
    document: Mapping[str, object], allowed: set[str], label: str
) -> None:
    if any(field not in allowed for field in document):
        raise AdmissionError(f"{label} contains an unsupported field")


def _relative_path(document: Mapping[str, object], field: str) -> str:
    value = _required_text(document, field)
    if (
        value.startswith("/")
        or value.endswith("/")
        or "\\" in value
        or "//" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise AdmissionError(f"{field} must be a safe relative path")
    return value


def _relative_string_list(
    document: Mapping[str, object], field: str, label: str
) -> list[str]:
    values = _required_string_list(document, field)
    normalized = [_relative_path({field: value}, field) for value in values]
    if len(set(normalized)) != len(normalized):
        raise AdmissionError(f"{label} must not contain duplicates")
    return sorted(normalized)


def _target_list(document: Mapping[str, object], field: str) -> list[str]:
    values = _required_string_list(document, field)
    if any(value not in PRIVATE_TARGETS for value in values):
        raise AdmissionError(f"{field} contains an unsupported target")
    if len(set(values)) != len(values):
        raise AdmissionError(f"{field} must not contain duplicates")
    return sorted(values)


def _private_value_present(value: object) -> bool:
    if isinstance(value, str):
        return bool(PRIVATE_STRING_PATTERN.search(value))
    if isinstance(value, Mapping):
        return any(_private_value_present(item) for item in value.values())
    if isinstance(value, list):
        return any(_private_value_present(item) for item in value)
    return False


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "plan", "admit", "apply"))
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument(
        "--projection",
        type=Path,
        help="optional projection path; apply can use the candidate's embedded projection",
    )
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--mode", choices=("public", "private", "both"))
    parser.add_argument("--overlay-path", type=Path)
    parser.add_argument("--private-root", type=Path)
    parser.add_argument("--target-root", type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="authorize the apply command after validation and preflight",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the report-only or explicitly approved JAS admission boundary."""

    args = _parser().parse_args(argv)
    candidate_result: dict[str, object] | None = None
    try:
        root = args.root.expanduser().resolve()
        candidate = load_json(args.candidate.expanduser().resolve())
        candidate_result = validate_candidate(candidate)
        try:
            projection = _projection_from_candidate(
                candidate,
                None if args.projection is None else args.projection.expanduser().resolve(),
            )
        except AdmissionError as exc:
            if args.command == "validate" and args.projection is None and "no embedded sanitized promotion projection" in str(exc):
                payload = {
                    "status": "review_required",
                    "admission_status": "review_required",
                    "candidate_structurally_valid": True,
                    "candidate_state": "candidate",
                    "candidate_id": candidate_result["candidate_id"],
                    "asset_id": None,
                    "visibility": "private",
                    "schema_version": None,
                    "reason": "promotion_projection_missing",
                    "projection_status": "missing",
                    "target": None,
                    "mutated": False,
                }
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
                return 0
            raise
        projection_result = validate_projection(
            projection,
            root,
            str(candidate_result["candidate_id"]),
            candidate_result,
        )
        if args.command == "validate":
            is_legacy_private = (
                projection_result["visibility"] == "private-overlay"
                and projection_result["schema_version"] == PROJECTION_SCHEMA_VERSION
            )
            payload: dict[str, object] = {
                "status": "blocked" if is_legacy_private else "review_required",
                "admission_status": "blocked" if is_legacy_private else "review_required",
                "candidate_structurally_valid": True,
                "candidate_state": "candidate",
                "candidate_id": candidate_result["candidate_id"],
                "asset_id": projection_result["asset_id"],
                "visibility": projection_result["visibility"],
                "schema_version": projection_result["schema_version"],
                "projection_status": "present",
                "reason": (
                    "private_overlay_requires_catalog_asset_reference"
                    if is_legacy_private
                    else None
                ),
                "target": (
                    "private-overlay.json"
                    if projection_result["visibility"] == "private-overlay"
                    else "catalog/manifest.json"
                ),
                "mutated": False,
            }
        elif args.command == "apply":
            if args.mode is None:
                raise AdmissionError("apply requires --mode public, private, or both")
            if args.approval is None:
                raise AdmissionError("apply requires explicit --approval")
            approval = load_json(args.approval.expanduser().resolve())
            payload = apply_admission(
                root,
                candidate,
                projection,
                approval,
                mode=str(args.mode),
                apply=bool(args.apply),
                overlay_path=(
                    None
                    if args.overlay_path is None
                    else args.overlay_path.expanduser().resolve()
                ),
                private_root=(
                    None
                    if args.private_root is None
                    else args.private_root.expanduser().resolve()
                ),
                target_root=(
                    None
                    if args.target_root is None
                    else args.target_root.expanduser().resolve()
                ),
            )
        else:
            approval = None
            if args.approval is not None:
                approval = load_json(args.approval.expanduser().resolve())
            payload = build_plan(root, candidate, projection, approval)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if payload["status"] != "blocked" else 2
    except (AdmissionError, OSError, ValueError) as exc:
        error_text = str(exc)
        payload = {
            "status": "blocked",
            "admission_status": "blocked",
            "candidate_structurally_valid": candidate_result is not None,
            "candidate_state": candidate.get("status") if isinstance(candidate, Mapping) else "invalid",
            "projection_status": "not_evaluated",
            "mutated": False,
            "reason": "candidate_validation_failed"
            if candidate_result is None
            else "admission_validation_failed",
            "validation_errors": [item.strip() for item in error_text.split("; ") if item.strip()],
            "error": error_text,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
