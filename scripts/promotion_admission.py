#!/usr/bin/env python3
"""Validate leverage candidates and produce a sanitized JAS admission plan."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Mapping, cast

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.catalog_validation import load_manifest, validate_manifest  # noqa: E402
from scripts.promotion_admission_contracts import (  # noqa: E402
    AdmissionError,
    PRIVATE_OVERLAY_SCHEMA_VERSION,
    PRIVATE_PROJECTION_SCHEMA_VERSION,
    PROJECTION_SCHEMA_VERSION,
    PUBLIC_SOURCE_ID,
    _private_overlay,
    _public_overlay,
    _required_text,
    build_plan,
    candidate_preflight_findings,
    load_json,
    validate_approval,
    validate_candidate,
    validate_projection,
)


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
        preflight_findings = candidate_preflight_findings(candidate)
        if preflight_findings:
            payload = {
                "status": "blocked",
                "reasons": preflight_findings,
                "mutated": False,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
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
