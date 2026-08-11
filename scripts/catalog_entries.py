#!/usr/bin/env python3
"""Project catalog assets into human-facing multiplier entries."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

TAXONOMY_RELATIVE_PATH = Path("catalog/taxonomy.json")


def load_taxonomy(root: Path) -> dict[str, Any]:
    """Load the catalog taxonomy from a repository root."""

    path = root / TAXONOMY_RELATIVE_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{path}: missing taxonomy") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: taxonomy root must be an object")
    return value


def entry_type(asset: dict[str, Any], taxonomy: dict[str, Any]) -> str:
    """Resolve an editorial type without changing the asset's runtime kind."""

    editorial = asset.get("editorial")
    if isinstance(editorial, dict) and isinstance(editorial.get("type"), str):
        return editorial["type"]
    defaults = taxonomy.get("kind_defaults", {})
    if isinstance(defaults, dict) and isinstance(defaults.get(asset.get("kind")), str):
        return defaults[asset["kind"]]
    return "reference"


def project_entry(
    asset: dict[str, Any], taxonomy: dict[str, Any]
) -> dict[str, Any]:
    """Return a stable public asset copy with derived editorial metadata."""

    projected = copy.deepcopy(asset)
    editorial = asset.get("editorial")
    editorial = editorial if isinstance(editorial, dict) else {}
    capabilities = asset.get("capabilities")
    default_topics = capabilities if isinstance(capabilities, list) else []
    topics = editorial.get("topics", default_topics)
    use_cases = editorial.get("use_cases", [])
    entrypoints = asset.get("entrypoints")
    source_path = None
    if isinstance(entrypoints, list) and entrypoints:
        source_path = str(Path(entrypoints[0]).parent)
    projected["entry"] = {
        "type": entry_type(asset, taxonomy),
        "topics": sorted(set(topics)) if isinstance(topics, list) else [],
        "use_cases": sorted(set(use_cases)) if isinstance(use_cases, list) else [],
        "why": editorial.get("why", asset.get("summary")),
        "use_when": editorial.get("use_when"),
        "avoid_when": editorial.get("avoid_when"),
        "source_path": source_path,
    }
    return projected


def featured_ids(taxonomy: dict[str, Any]) -> set[str]:
    """Return all entry IDs intentionally placed in a collection."""

    result: set[str] = set()
    collections = taxonomy.get("collections")
    if not isinstance(collections, list):
        return result
    for collection in collections:
        if not isinstance(collection, dict):
            continue
        entries = collection.get("entries")
        if isinstance(entries, list):
            result.update(item for item in entries if isinstance(item, str))
    return result
