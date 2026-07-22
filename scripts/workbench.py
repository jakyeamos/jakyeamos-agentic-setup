#!/usr/bin/env python3
"""Inspect and stage the Portable Agentic Workbench catalog."""

from __future__ import annotations

import argparse
import copy
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
    ):
        value = asset.get(key)
        if isinstance(value, list):
            fields.extend(str(item) for item in value)
        elif value is not None:
            fields.append(str(value))
    return " ".join(fields).casefold().replace("-", " ")


def _list_assets(root: Path) -> dict[str, Any]:
    manifest = load_manifest(root)
    return {
        "schema_version": manifest.get("schema_version"),
        "workbench_version": manifest.get("workbench", {}).get("version"),
        "assets": [_public_asset(asset) for asset in _manifest_assets(root)],
    }


def _public_asset(asset: dict[str, Any]) -> dict[str, Any]:
    """Return a stable copy of an asset record."""

    return copy.deepcopy(asset)


def _search_assets(root: Path, query: str) -> dict[str, Any]:
    normalized = query.casefold().strip()
    if not normalized:
        raise WorkbenchError("search query must not be empty")
    tokens = normalized.replace("-", " ").split()
    matches = [
        _public_asset(asset)
        for asset in _manifest_assets(root)
        if all(token in _search_text(asset) for token in tokens)
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
    plan["dry_run"] = False
    return plan


def _run_validation(root: Path) -> list[str]:
    errors = validate_manifest(root)
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

    validate_parser = subparsers.add_parser(
        "validate", help="validate catalog, public safety, prevention pack, and skills"
    )
    validate_parser.add_argument(
        "--json", action="store_true", help="emit deterministic JSON"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a workbench command and return its process status."""

    args = _parser().parse_args(argv)
    try:
        if args.command == "list":
            payload = _list_assets(ROOT)
            human = [
                f"{asset['id']}\t{asset['title']}\t{asset['asset_class']}"
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
            asset = _public_asset(_find_asset(ROOT, args.asset_id))
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
