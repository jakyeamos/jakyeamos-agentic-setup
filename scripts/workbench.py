#!/usr/bin/env python3
"""Inspect and stage the Portable Agentic Workbench catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INSTALL_TARGETS = ("generic", "codex", "claude", "gemini", "cursor", "antigravity", "copilot")
if not __package__:
    sys.path.insert(0, str(ROOT))

# Direct script execution bootstraps the repository root before package imports.
from scripts.catalog_validation import load_manifest, validate_manifest  # noqa: E402
from scripts.catalog_entries import (  # noqa: E402
    featured_ids,
    load_taxonomy,
    project_entry,
)
from scripts.catalog_index import INDEX_RELATIVE_PATH, render_index, validate_index  # noqa: E402
from scripts.public_safety_check import scan_repository  # noqa: E402
from scripts.validate_prevention_pack import validate_prevention_pack  # noqa: E402
from scripts.validate_skills import validate_skill  # noqa: E402


class WorkbenchError(ValueError):
    """An expected command or catalog error."""


def _manifest_assets(root: Path) -> list[dict[str, Any]]:
    manifest = load_manifest(root)
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise WorkbenchError("catalog assets must be a list")
    return sorted(
        (asset for asset in assets if isinstance(asset, dict)),
        key=lambda item: item.get("id", ""),
    )


def _find_asset(root: Path, asset_id: str) -> dict[str, Any]:
    for asset in _manifest_assets(root):
        if asset.get("id") == asset_id:
            return asset
    raise WorkbenchError(f"unknown asset: {asset_id}")


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _emit(value: Any, as_json: bool, human_lines: list[str]) -> None:
    if as_json:
        print(_json_text(value), end="")
    else:
        print("\n".join(human_lines))


def _search_text(asset: dict[str, Any]) -> str:
    fields: list[str] = []
    for key in (
        "id",
        "kind",
        "asset_class",
        "title",
        "summary",
        "maturity",
        "capabilities",
        "supported_targets",
        "entry",
    ):
        value = asset.get(key)
        if isinstance(value, list):
            fields.extend(str(item) for item in value)
        elif isinstance(value, dict):
            for nested in value.values():
                if isinstance(nested, list):
                    fields.extend(str(item) for item in nested)
                elif nested is not None:
                    fields.append(str(nested))
        elif value is not None:
            fields.append(str(value))
    return " ".join(fields).casefold().replace("-", " ")


def _list_assets(
    root: Path,
    entry_type_filter: str | None = None,
    topic: str | None = None,
    featured: bool = False,
) -> dict[str, Any]:
    manifest = load_manifest(root)
    taxonomy = load_taxonomy(root)
    assets = [_public_asset(asset, taxonomy) for asset in _manifest_assets(root)]
    valid_types = {
        item.get("id")
        for item in taxonomy.get("types", [])
        if isinstance(item, dict)
    }
    if entry_type_filter is not None:
        if entry_type_filter not in valid_types:
            raise WorkbenchError(f"unknown entry type: {entry_type_filter}")
        assets = [
            asset
            for asset in assets
            if asset["entry"]["type"] == entry_type_filter
        ]
    if topic is not None:
        assets = [asset for asset in assets if topic in asset["entry"]["topics"]]
    if featured:
        selected = featured_ids(taxonomy)
        assets = [asset for asset in assets if asset["id"] in selected]
    return {
        "schema_version": manifest.get("schema_version"),
        "workbench_version": manifest.get("workbench", {}).get("version"),
        "filters": {
            "type": entry_type_filter,
            "topic": topic,
            "featured": featured,
        },
        "count": len(assets),
        "assets": assets,
    }


def _public_asset(
    asset: dict[str, Any], taxonomy: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Return a stable asset copy with its editorial entry projection."""

    return project_entry(asset, taxonomy or load_taxonomy(ROOT))


def _search_assets(root: Path, query: str) -> dict[str, Any]:
    normalized = query.casefold().strip()
    if not normalized:
        raise WorkbenchError("search query must not be empty")
    tokens = normalized.replace("-", " ").split()
    taxonomy = load_taxonomy(root)
    projected = [_public_asset(asset, taxonomy) for asset in _manifest_assets(root)]
    matches = [
        asset for asset in projected if all(token in _search_text(asset) for token in tokens)
    ]
    return {"query": query, "count": len(matches), "assets": matches}


def _source_root(asset: dict[str, Any]) -> Path:
    entrypoints = asset.get("entrypoints", [])
    if entrypoints:
        return Path(entrypoints[0]).parent
    files = asset.get("files", [])
    if files:
        return Path(files[0]).parent
    return Path(".")


def _install_relative_path(asset: dict[str, Any], source: str) -> Path:
    install = asset.get("install", {})
    path_map = install.get("path_map", {}) if isinstance(install, dict) else {}
    if isinstance(path_map, dict) and source in path_map:
        return Path(path_map[source])
    source_path = Path(source)
    source_root = _source_root(asset)
    try:
        return source_path.relative_to(source_root)
    except ValueError:
        return Path(source_path.name)


def _dependency_report(asset: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    dependencies: list[dict[str, Any]] = []
    required_missing = False
    for dependency in asset.get("dependencies", []):
        if not isinstance(dependency, dict):
            continue
        command = dependency.get("command")
        available = (
            shutil.which(command) is not None if isinstance(command, str) else None
        )
        item = {
            "available": available,
            "command": command,
            "kind": dependency.get("kind"),
            "name": dependency.get("name"),
            "required": dependency.get("required", False),
        }
        dependencies.append(item)
        if available is False and dependency.get("required") is True:
            required_missing = True
    return dependencies, required_missing


def _safe_destination(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise WorkbenchError(f"installation path escapes target root: {relative}")
    destination = (root / relative).resolve()
    try:
        destination.relative_to(root.resolve())
    except ValueError as exc:
        raise WorkbenchError(
            f"installation path escapes target root: {relative}"
        ) from exc
    return destination


def _install_plan(
    root: Path, asset: dict[str, Any], target: str, dry_run: bool
) -> dict[str, Any]:
    if target not in INSTALL_TARGETS:
        raise WorkbenchError(f"unsupported installation target: {target}")
    supported_targets = asset.get("supported_targets", [])
    if target not in supported_targets:
        raise WorkbenchError(
            f"asset {asset.get('id')} does not support target {target}"
        )

    install = asset.get("install", {})
    if not isinstance(install, dict):
        raise WorkbenchError(f"asset {asset.get('id')} has an invalid install record")
    mode = install.get("mode")
    dependencies, required_missing = _dependency_report(asset)
    actions: list[dict[str, Any]] = []
    if mode in {"copy", "stage"}:
        destination_root = _safe_destination(
            root, Path(str(install.get("destination", "")))
        )
        for source in sorted(asset.get("files", [])):
            relative_destination = _install_relative_path(asset, source)
            destination = _safe_destination(destination_root, relative_destination)
            action_status = (
                "exists"
                if destination.exists()
                else ("would-copy" if dry_run else "ready")
            )
            actions.append(
                {
                    "destination": str(destination),
                    "source": source,
                    "status": action_status,
                }
            )

    existing = [action for action in actions if action["status"] == "exists"]
    if mode == "manual":
        status = "manual-review"
    elif required_missing:
        status = "blocked-missing-required-dependency"
    elif existing:
        status = "blocked-existing-files"
    else:
        status = "ready"

    return {
        "asset_id": asset.get("id"),
        "dependencies": dependencies,
        "dry_run": dry_run,
        "install_mode": mode,
        "manual_review": install.get("manual_review"),
        "root": str(root),
        "status": status,
        "target": target,
        "actions": actions,
    }


def _apply_install(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    if plan["status"] != "ready":
        return plan
    if plan["install_mode"] == "manual":
        return plan
    root.mkdir(parents=True, exist_ok=True)
    for action in plan["actions"]:
        source_path = ROOT / action["source"]
        destination = Path(action["destination"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        action["status"] = "copied"
    receipt_path = root / ".workbench-receipts" / f"{plan['asset_id']}.json"
    receipt = {
        "schema_version": "portable-workbench-receipt/v1",
        "asset_id": plan["asset_id"],
        "target": plan["target"],
        "install_mode": plan["install_mode"],
        "files": [
            {
                "path": str(Path(action["destination"]).relative_to(root)),
                "sha256": _sha256(Path(action["destination"])),
                "source": action["source"],
            }
            for action in plan["actions"]
        ],
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(_json_text(receipt), encoding="utf-8")
    plan["receipt"] = str(receipt_path)
    plan["dry_run"] = False
    return plan


def _uninstall_plan(
    root: Path,
    asset: dict[str, Any],
    target: str,
    dry_run: bool,
    receipt_path: Path | None = None,
) -> dict[str, Any]:
    """Plan a receipt-scoped uninstall without deleting modified files."""

    if target not in INSTALL_TARGETS:
        raise WorkbenchError(f"unsupported installation target: {target}")
    supported_targets = asset.get("supported_targets", [])
    if target not in supported_targets:
        raise WorkbenchError(
            f"asset {asset.get('id')} does not support target {target}"
        )
    install = asset.get("install", {})
    if not isinstance(install, dict):
        raise WorkbenchError(f"asset {asset.get('id')} has an invalid install record")
    mode = install.get("mode")
    receipt = (receipt_path or (root / ".workbench-receipts" / f"{asset.get('id')}.json")).resolve()
    base: dict[str, Any] = {
        "asset_id": asset.get("id"),
        "dry_run": dry_run,
        "install_mode": mode,
        "operation": "uninstall",
        "receipt": str(receipt),
        "root": str(root),
        "target": target,
        "actions": [],
        "mutated": False,
    }
    if mode not in {"copy", "stage"}:
        base.update(
            status="blocked-uninstall-safety",
            reason="unsupported_install_mode",
        )
        return base
    if not receipt.is_file() or receipt.is_symlink():
        base.update(status="blocked-uninstall-safety", reason="receipt_missing")
        return base
    try:
        receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base.update(status="blocked-uninstall-safety", reason="receipt_invalid")
        base["receipt_error"] = str(exc)
        return base
    if not isinstance(receipt_value, dict) or receipt_value.get("asset_id") != asset.get("id"):
        base.update(status="blocked-uninstall-safety", reason="receipt_identity_mismatch")
        return base
    receipt_files = receipt_value.get("files")
    expected_by_source = {
        item.get("source"): item
        for item in receipt_files
        if isinstance(item, dict) and isinstance(item.get("source"), str)
    } if isinstance(receipt_files, list) else {}
    try:
        destination_root = _safe_destination(
            root, Path(str(install.get("destination", "")))
        )
    except WorkbenchError:
        base.update(status="blocked-uninstall-safety", reason="unsafe_destination")
        return base
    unsafe = False
    for source in sorted(asset.get("files", [])):
        relative_destination = _install_relative_path(asset, source)
        destination = _safe_destination(destination_root, relative_destination)
        receipt_item = expected_by_source.get(source)
        expected_hash = receipt_item.get("sha256") if isinstance(receipt_item, dict) else None
        relative_path = str(destination.relative_to(root))
        if not destination.exists():
            action_status = "missing"
            unsafe = True
        elif not destination.is_file() or destination.is_symlink():
            action_status = "modified"
            unsafe = True
        elif not isinstance(expected_hash, str) or _sha256(destination) != expected_hash:
            action_status = "modified"
            unsafe = True
        else:
            action_status = "ready-remove"
        base["actions"].append(
            {
                "destination": str(destination),
                "path": relative_path,
                "source": source,
                "status": action_status,
            }
        )
    base["status"] = "blocked-uninstall-safety" if unsafe else "ready-uninstall"
    if unsafe:
        base["reason"] = "receipt_hash_or_file_state_mismatch"
    return base


def _apply_uninstall(plan: dict[str, Any]) -> dict[str, Any]:
    if plan["status"] != "ready-uninstall":
        return plan
    for action in plan["actions"]:
        destination = Path(action["destination"])
        if destination.exists():
            destination.unlink()
        action["status"] = "removed"
    plan["dry_run"] = False
    plan["mutated"] = bool(plan["actions"])
    return plan


def _run_validation(root: Path) -> list[str]:
    errors = validate_manifest(root)
    errors.extend(validate_index(root))
    errors.extend(scan_repository(root))
    if root.resolve() == ROOT.resolve():
        errors.extend(validate_prevention_pack(root))
        for skill_dir in sorted(
            path for path in (root / "skills").iterdir() if path.is_dir()
        ):
            errors.extend(validate_skill(skill_dir))
    return errors


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list catalog assets")
    list_parser.add_argument(
        "--json", action="store_true", help="emit deterministic JSON"
    )
    list_parser.add_argument("--type", dest="entry_type", help="filter by entry type")
    list_parser.add_argument("--topic", help="filter by exact topic slug")
    list_parser.add_argument(
        "--featured", action="store_true", help="show entries in curated collections"
    )

    search_parser = subparsers.add_parser("search", help="search catalog metadata")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument(
        "--json", action="store_true", help="emit deterministic JSON"
    )

    show_parser = subparsers.add_parser("show", help="show one catalog asset")
    show_parser.add_argument("asset_id")
    show_parser.add_argument(
        "--json", action="store_true", help="emit deterministic JSON"
    )

    install_parser = subparsers.add_parser(
        "install", help="plan or apply a safe asset installation"
    )
    install_parser.add_argument("asset_id")
    install_parser.add_argument("--target", required=True, choices=INSTALL_TARGETS)
    install_parser.add_argument("--root", required=True, type=Path)
    install_mode = install_parser.add_mutually_exclusive_group()
    install_mode.add_argument(
        "--dry-run", action="store_true", help="preview only; this is the default"
    )
    install_mode.add_argument(
        "--apply", action="store_true", help="copy into the explicit target root"
    )
    install_parser.add_argument(
        "--json", action="store_true", help="emit deterministic JSON"
    )

    uninstall_parser = subparsers.add_parser(
        "uninstall", help="plan or apply a receipt-scoped safe asset uninstall"
    )
    uninstall_parser.add_argument("asset_id")
    uninstall_parser.add_argument("--target", required=True, choices=INSTALL_TARGETS)
    uninstall_parser.add_argument("--root", required=True, type=Path)
    uninstall_parser.add_argument("--receipt", type=Path)
    uninstall_mode = uninstall_parser.add_mutually_exclusive_group()
    uninstall_mode.add_argument(
        "--dry-run", action="store_true", help="preview only; this is the default"
    )
    uninstall_mode.add_argument(
        "--apply", action="store_true", help="remove only unchanged receipt-scoped files"
    )
    uninstall_parser.add_argument(
        "--json", action="store_true", help="emit deterministic JSON"
    )

    validate_parser = subparsers.add_parser(
        "validate", help="validate catalog, public safety, prevention pack, and skills"
    )
    validate_parser.add_argument(
        "--json", action="store_true", help="emit deterministic JSON"
    )
    index_parser = subparsers.add_parser(
        "index", help="render, check, or update the generated human catalog"
    )
    index_mode = index_parser.add_mutually_exclusive_group()
    index_mode.add_argument(
        "--check", action="store_true", help="fail when catalog/index.md is stale"
    )
    index_mode.add_argument(
        "--write", action="store_true", help="update catalog/index.md"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a workbench command and return its process status."""

    args = _parser().parse_args(argv)
    try:
        if args.command == "list":
            payload = _list_assets(
                ROOT,
                entry_type_filter=args.entry_type,
                topic=args.topic,
                featured=args.featured,
            )
            human = [
                f"{asset['id']}\t{asset['title']}\t{asset['entry']['type']}"
                for asset in payload["assets"]
            ]
            _emit(payload, args.json, human)
            return 0
        if args.command == "search":
            payload = _search_assets(ROOT, args.query)
            human = [f"{asset['id']}\t{asset['title']}" for asset in payload["assets"]]
            _emit(payload, args.json, human)
            return 0
        if args.command == "show":
            asset = _public_asset(_find_asset(ROOT, args.asset_id), load_taxonomy(ROOT))
            _emit(
                asset, args.json, [f"{asset['id']}: {asset['title']}", asset["summary"]]
            )
            return 0
        if args.command == "install":
            root = args.root.expanduser().resolve()
            if root == Path("/") or root == Path.home():
                raise WorkbenchError(
                    "refusing an installation root that is the filesystem or user home"
                )
            asset = _find_asset(ROOT, args.asset_id)
            dry_run = not args.apply
            plan = _install_plan(root, asset, args.target, dry_run)
            if args.apply and plan["status"] == "ready":
                plan = _apply_install(root, plan)
            human = [
                f"{plan['asset_id']}: {plan['status']}",
                f"target root: {plan['root']}",
                f"mode: {plan['install_mode']}",
            ]
            human.extend(
                f"{action['status']}: {action['source']} -> {action['destination']}"
                for action in plan["actions"]
            )
            if plan.get("manual_review"):
                human.append(f"manual review: {plan['manual_review']}")
            _emit(plan, args.json, human)
            return 1 if plan["status"].startswith("blocked") else 0
        if args.command == "uninstall":
            root = args.root.expanduser().resolve()
            if root == Path("/") or root == Path.home():
                raise WorkbenchError(
                    "refusing an uninstall root that is the filesystem or user home"
                )
            asset = _find_asset(ROOT, args.asset_id)
            plan = _uninstall_plan(
                root,
                asset,
                args.target,
                not args.apply,
                None if args.receipt is None else args.receipt.expanduser(),
            )
            if args.apply and plan["status"] == "ready-uninstall":
                plan = _apply_uninstall(plan)
            human = [
                f"{plan['asset_id']}: {plan['status']}",
                f"target root: {plan['root']}",
                f"operation: {plan['operation']}",
                f"dry-run: {plan['dry_run']}",
            ]
            human.extend(
                f"{action['status']}: {action['source']} -> {action['destination']}"
                for action in plan["actions"]
            )
            _emit(plan, args.json, human)
            return 1 if plan["status"].startswith("blocked") else 0
        if args.command == "index":
            rendered = render_index(ROOT)
            if args.write:
                (ROOT / INDEX_RELATIVE_PATH).write_text(rendered, encoding="utf-8")
                print(f"updated {INDEX_RELATIVE_PATH}")
                return 0
            if args.check:
                errors = validate_index(ROOT)
                if errors:
                    print("\n".join(errors), file=sys.stderr)
                    return 1
                print("catalog index is current")
                return 0
            print(rendered, end="")
            return 0
        if args.command == "validate":
            errors = _run_validation(ROOT)
            payload = {
                "catalog": not any(
                    error.startswith(("asset ", "catalog/", "source_map"))
                    for error in errors
                ),
                "errors": errors,
                "skills": not any(
                    error.startswith(str(ROOT / "skills")) for error in errors
                ),
                "safety": not any(
                    "private" in error
                    or "credential" in error
                    or "authorization" in error
                    or "secret" in error
                    or "environment file" in error
                    for error in errors
                ),
                "ok": not errors,
            }
            if args.json:
                print(_json_text(payload), end="")
            elif errors:
                for error in errors:
                    print(error)
            else:
                print("workbench validation ok")
            return 1 if errors else 0
    except (OSError, WorkbenchError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
