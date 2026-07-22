#!/usr/bin/env python3
"""Validate the shared environment-legibility prevention contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if not __package__:
    sys.path.insert(0, str(ROOT))

from scripts.catalog_validation import load_manifest  # noqa: E402


WORKFLOW_MARKERS: dict[str, tuple[str, ...]] = {
    "workflows/repo-aware-context/WORKFLOW.md": (
        "identity and freshness gate",
        "checkout identity",
        "minimum-context gate",
        "unknown",
        "stale",
        "blocked",
        "disposable",
        "whole repository",
    ),
    "workflows/safe-tool-guards/WORKFLOW.md": (
        "dirty",
        "detached",
        "prunable",
        "disposable",
        "approval",
        "credential",
        "timeout",
        "raw command output",
        "owner",
        "removal condition",
    ),
    "workflows/safe-tool-guards/CONTRACT.md": (
        '"action"',
        '"targets"',
        '"dry_run"',
        '"approval"',
        "blocked",
        "unavailable",
        "timeout",
        "public",
        "credential",
    ),
    "workflows/environment-legibility-audit/WORKFLOW.md": (
        "missing-context-index",
        "missing-approval-path-contract",
        "missing-security-contract",
        "unverified-quality-commands",
        "owner:",
        "validation:",
        "removal condition:",
        "replay",
        "manual review",
        "timeout",
        "pre-cr",
        "quality runner",
    ),
}

REQUIRED_ASSETS: dict[str, tuple[str, ...]] = {
    "repo-aware-context": ("workflows/repo-aware-context/WORKFLOW.md",),
    "environment-legibility-audit": (
        "workflows/environment-legibility-audit/WORKFLOW.md",
    ),
    "safe-tool-guards": (
        "workflows/safe-tool-guards/CONTRACT.md",
        "workflows/safe-tool-guards/WORKFLOW.md",
    ),
}

SUPPORTED_TARGETS = {
    "generic",
    "codex",
    "claude",
    "cursor",
    "copilot",
    "gemini",
    "antigravity",
}


def _asset_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        return {}
    return {
        str(asset.get("id")): asset
        for asset in assets
        if isinstance(asset, dict) and isinstance(asset.get("id"), str)
    }


def _relative_file(root: Path, relative: str) -> Path:
    return root / Path(relative)


def _validate_workflow_files(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, markers in WORKFLOW_MARKERS.items():
        path = _relative_file(root, relative)
        if not path.is_file():
            errors.append(f"{relative}: required prevention file is missing")
            continue
        text = path.read_text(encoding="utf-8", errors="replace").casefold()
        for marker in markers:
            if marker.casefold() not in text:
                errors.append(f"{relative}: missing prevention marker {marker}")
    return errors


def _validate_assets(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_manifest(root)
    except ValueError as exc:
        return [str(exc)]

    assets = _asset_map(manifest)
    for asset_id, required_files in REQUIRED_ASSETS.items():
        asset = assets.get(asset_id)
        if asset is None:
            errors.append(f"catalog/manifest.json: missing prevention asset {asset_id}")
            continue
        if asset.get("kind") != "workflow":
            errors.append(f"{asset_id}: prevention asset must be a workflow")
        targets = asset.get("supported_targets")
        target_set = (
            {target for target in targets if isinstance(target, str)}
            if isinstance(targets, list)
            else set()
        )
        if (
            not isinstance(targets, list)
            or len(target_set) != len(targets)
            or target_set != SUPPORTED_TARGETS
        ):
            errors.append(
                f"{asset_id}: supported_targets must cover the shared target set"
            )
        files = asset.get("files")
        if not isinstance(files, list):
            errors.append(f"{asset_id}: files must be a list")
        else:
            for required_file in required_files:
                if required_file not in files:
                    errors.append(f"{asset_id}: manifest omits {required_file}")
        evidence = asset.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{asset_id}: evidence is required")
        validation = asset.get("validation")
        if not isinstance(validation, list) or not validation:
            errors.append(f"{asset_id}: executable validation metadata is required")
        install = asset.get("install")
        if not isinstance(install, dict) or install.get("mode") != "copy":
            errors.append(f"{asset_id}: prevention workflow must use copy install mode")
        elif not isinstance(install.get("manual_review"), str) or not install.get(
            "manual_review"
        ):
            errors.append(f"{asset_id}: manual review installation text is required")

    environment = assets.get("environment-legibility-audit")
    if isinstance(environment, dict):
        validation = environment.get("validation", [])
        if not any(
            isinstance(item, str)
            and item == "python3 scripts/validate_prevention_pack.py"
            for item in validation
        ):
            errors.append(
                "environment-legibility-audit: validation must run the prevention validator"
            )
    return errors


def validate_prevention_pack(root: Path = ROOT) -> list[str]:
    """Return deterministic validation errors for the shared prevention pack."""

    errors = _validate_workflow_files(root)
    errors.extend(_validate_assets(root))
    return sorted(set(errors))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the prevention-pack validation."""

    args = _parser().parse_args(argv)
    errors = validate_prevention_pack(args.root.resolve())
    payload = {"errors": errors, "ok": not errors}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif errors:
        print("\n".join(errors))
    else:
        print("prevention pack validation ok")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
