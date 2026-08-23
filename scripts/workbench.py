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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _receipt_path(root: Path, asset: dict[str, Any], target: str) -> Path:
    asset_id = str(asset.get("id", ""))
    if not asset_id or Path(asset_id).name != asset_id:
        raise WorkbenchError(f"asset {asset_id!r} cannot have an install receipt")
    return _safe_destination(
        root, Path(".workbench-receipts") / f"{asset_id}.json"
    )


def _install_receipt(asset: dict[str, Any], target: str) -> dict[str, Any]:
    files: list[dict[str, str]] = []
    for source in sorted(asset.get("files", [])):
        source_path = ROOT / source
        if not source_path.is_file():
            raise WorkbenchError(f"manifest source is not a file: {source}")
        files.append(
            {
                "destination": _install_relative_path(asset, source).as_posix(),
                "sha256": _sha256_file(source_path),
                "source": source,
            }
        )
    install = asset.get("install", {})
    return {
        "asset_id": asset.get("id"),
        "destination": str(install.get("destination", "")),
        "files": files,
        "install_mode": install.get("mode"),
        "schema_version": 1,
        "target": target,
    }


def _receipt_matches(
    receipt: Any,
    asset: dict[str, Any],
    target: str,
    expected_destination: str,
) -> bool:
    if not isinstance(receipt, dict):
        return False
    install = asset.get("install", {})
    expected_files = [
        {
            "destination": _install_relative_path(asset, source).as_posix(),
            "source": source,
        }
        for source in sorted(asset.get("files", []))
    ]
    actual_files = receipt.get("files")
    if not isinstance(actual_files, list):
        return False
    if receipt.get("schema_version") != 1:
        return False
    if receipt.get("asset_id") != asset.get("id"):
        return False
    if receipt.get("target") != target:
        return False
    if receipt.get("install_mode") != install.get("mode"):
        return False
    if receipt.get("destination") != expected_destination:
        return False
    if len(actual_files) != len(expected_files):
        return False
    for expected, actual in zip(expected_files, actual_files):
        if not isinstance(actual, dict):
            return False
        if actual.get("source") != expected["source"]:
            return False
        if actual.get("destination") != expected["destination"]:
            return False
        if not isinstance(actual.get("sha256"), str) or len(actual["sha256"]) != 64:
            return False
    return True


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
    receipt: dict[str, Any] | None = None
    receipt_exists = False
    if mode in {"copy", "stage"}:
        destination_root = _safe_destination(
            root, Path(str(install.get("destination", "")))
        )
        receipt_path = _receipt_path(root, asset, target)
        receipt_exists = receipt_path.exists() or receipt_path.is_symlink()
        receipt = {
            "path": str(receipt_path),
            "status": "exists" if receipt_exists else "would-write" if dry_run else "ready",
        }
        for source in sorted(asset.get("files", [])):
            relative_destination = _install_relative_path(asset, source)
            destination = _safe_destination(destination_root, relative_destination)
            source_missing = not (ROOT / source).is_file()
            action_status = "missing-source" if source_missing else (
                "exists" if destination.exists() else ("would-copy" if dry_run else "ready")
            )
            actions.append(
                {
                    "destination": str(destination),
                    "source": source,
                    "status": action_status,
                }
            )

    existing = [action for action in actions if action["status"] == "exists"]
    missing_sources = [
        action for action in actions if action["status"] == "missing-source"
    ]
    if mode == "manual":
        status = "manual-review"
    elif missing_sources:
        status = "blocked-missing-source"
    elif required_missing:
        status = "blocked-missing-required-dependency"
    elif receipt_exists:
        status = "blocked-existing-receipt"
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
        "receipt": receipt,
    }


def _apply_install(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    if plan["status"] != "ready":
        return plan
    if plan["install_mode"] == "manual":
        return plan
    root.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for action in plan["actions"]:
        source_path = ROOT / action["source"]
        destination = Path(action["destination"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source_path, destination)
        except Exception:
            for copied_path in reversed(copied):
                if copied_path.is_file() and not copied_path.is_symlink():
                    copied_path.unlink()
            raise
        copied.append(destination)
        action["status"] = "copied"
    receipt_path = Path(plan["receipt"]["path"])
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    asset = _find_asset(ROOT, plan["asset_id"])
    receipt_payload = _install_receipt(asset, plan["target"])
    try:
        with receipt_path.open("x", encoding="utf-8") as handle:
            handle.write(_json_text(receipt_payload))
    except Exception:
        for copied_path in reversed(copied):
            if copied_path.is_file() and not copied_path.is_symlink():
                copied_path.unlink()
        raise
    plan["receipt"]["status"] = "written"
    plan["dry_run"] = False
    return plan


def _uninstall_plan(
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
    dependencies, _ = _dependency_report(asset)
    destination_root = _safe_destination(
        root, Path(str(install.get("destination", "")))
    ) if mode in {"copy", "stage"} else None
    receipt_path = _receipt_path(root, asset, target) if mode in {"copy", "stage"} else None
    actions: list[dict[str, Any]] = []
    receipt_payload: Any = None
    receipt_error: str | None = None
    if mode == "manual":
        return {
            "asset_id": asset.get("id"),
            "actions": actions,
            "dependencies": dependencies,
            "dry_run": dry_run,
            "install_mode": mode,
            "manual_review": install.get("manual_review"),
            "receipt": None,
            "root": str(root),
            "status": "manual-review",
            "target": target,
        }

    assert destination_root is not None
    assert receipt_path is not None
    receipt_exists = receipt_path.is_file() and not receipt_path.is_symlink()
    if receipt_exists:
        try:
            receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            receipt_error = f"unreadable install receipt: {exc}"
        if receipt_error is None and not _receipt_matches(
            receipt_payload,
            asset,
            target,
            str(install.get("destination", "")),
        ):
            receipt_error = "install receipt does not match the current manifest"

    expected_hashes: dict[str, str] = {}
    if receipt_error is None and isinstance(receipt_payload, dict):
        expected_hashes = {
            item["source"]: item["sha256"]
            for item in receipt_payload["files"]
            if isinstance(item, dict)
            and isinstance(item.get("source"), str)
            and isinstance(item.get("sha256"), str)
        }
    for source in sorted(asset.get("files", [])):
        relative_destination = _install_relative_path(asset, source)
        destination = _safe_destination(destination_root, relative_destination)
        if not destination.exists() and not destination.is_symlink():
            action_status = "absent"
        elif destination.is_symlink():
            action_status = "blocked-symlink"
        elif not destination.is_file():
            action_status = "blocked-non-file"
        elif receipt_error is not None or not receipt_exists:
            action_status = "unowned"
        elif _sha256_file(destination) != expected_hashes.get(source):
            action_status = "modified"
        else:
            action_status = "would-remove" if dry_run else "ready-to-remove"
        actions.append(
            {
                "destination": str(destination),
                "source": source,
                "status": action_status,
            }
        )

    unsafe = [
        action
        for action in actions
        if action["status"] in {"blocked-symlink", "blocked-non-file", "unowned", "modified"}
    ]
    all_absent = all(action["status"] == "absent" for action in actions)
    if mode not in {"copy", "stage"}:
        status = "manual-review"
    elif receipt_path.is_symlink() or (receipt_path.exists() and not receipt_exists):
        status = "blocked-invalid-receipt"
    elif receipt_error is not None:
        status = "blocked-invalid-receipt"
    elif unsafe:
        status = "blocked-uninstall-safety"
    elif not receipt_exists:
        status = "already-absent" if all_absent else "blocked-missing-receipt"
    else:
        status = "already-absent" if all_absent else "ready"

    receipt_status = None
    if receipt_exists:
        receipt_status = (
            "would-remove"
            if dry_run and not unsafe
            else "ready-to-remove"
            if not dry_run and not unsafe
            else "blocked"
        )
    return {
        "asset_id": asset.get("id"),
        "actions": actions,
        "dependencies": dependencies,
        "dry_run": dry_run,
        "install_mode": mode,
        "manual_review": install.get("manual_review"),
        "receipt": {
            "path": str(receipt_path),
            "status": receipt_status or "absent",
        },
        "root": str(root),
        "status": status,
        "target": target,
    }


def _apply_uninstall(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    if plan["status"] not in {"ready", "already-absent"}:
        return plan
    receipt_path = Path(plan["receipt"]["path"])
    for action in plan["actions"]:
        if action["status"] == "ready-to-remove":
            destination = Path(action["destination"])
            if destination.is_file() and not destination.is_symlink():
                destination.unlink()
                action["status"] = "removed"
    if receipt_path.is_file() and not receipt_path.is_symlink():
        receipt_path.unlink()
        plan["receipt"]["status"] = "removed"
    plan["dry_run"] = False
    plan["status"] = "uninstalled"
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
        "uninstall", help="plan or apply a receipt-scoped asset uninstall"
    )
    uninstall_parser.add_argument("asset_id")
    uninstall_parser.add_argument("--target", required=True, choices=INSTALL_TARGETS)
    uninstall_parser.add_argument("--root", required=True, type=Path)
    uninstall_mode = uninstall_parser.add_mutually_exclusive_group()
    uninstall_mode.add_argument(
        "--dry-run", action="store_true", help="preview only; this is the default"
    )
    uninstall_mode.add_argument(
        "--apply", action="store_true", help="remove only receipt-owned files"
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
            dry_run = not args.apply
            plan = _uninstall_plan(root, asset, args.target, dry_run)
            if args.apply and plan["status"] in {"ready", "already-absent"}:
                plan = _apply_uninstall(root, plan)
            human = [
                f"{plan['asset_id']}: {plan['status']}",
                f"target root: {plan['root']}",
                f"mode: {plan['install_mode']}",
            ]
            human.extend(
                f"{action['status']}: {action['source']} -> {action['destination']}"
                for action in plan["actions"]
            )
            if plan.get("receipt"):
                human.append(
                    f"receipt {plan['receipt']['status']}: {plan['receipt']['path']}"
                )
            if plan.get("manual_review"):
                human.append(f"manual review: {plan['manual_review']}")
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
