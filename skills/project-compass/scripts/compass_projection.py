"""Canonical, tolerant family projection. Invalid neighbors remain visible."""
from __future__ import annotations

from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import Path

from compass_sources import bindings, digest, file_digest, git, read_json, reference, source_identity

SCHEMA = "compass-family/v1"


def root_summary(contract: dict | None, error: str | None = None) -> dict:
    from project_compass import score_contract
    empty = {"progress_percent": None, "scored_outcome_count": 0, "covered_pillar_count": 0,
             "total_pillar_count": 0, "confidence": "unknown", "confidence_percent": 0}
    result = {"status": "Invalid" if error else "Missing", "contract_path": ".project-compass/contract.json",
              "revision": None, "updated_at": None, "project_name": None, "identity": None, "audience": None,
              "mvp": dict(empty), "complete_product": dict(empty), "open_blockers": 0, "open_drift": 0,
              "open_blocker_items": [], "open_drift_items": [], "error": error}
    if contract is None:
        return result
    scores = score_contract(contract)
    for target, score in scores.items():
        result[target] = {**empty, **{k: score[k] for k in ("progress_percent", "confidence", "confidence_percent")},
                          "scored_outcome_count": sum(len(v) for v in score["score_inputs"].values()),
                          "covered_pillar_count": sum(bool(v) for v in score["score_inputs"].values()),
                          "total_pillar_count": len(contract["pillars"])}
    blockers = [{"outcome_id": o["id"], "outcome_name": o["name"], **b}
                for p in contract["pillars"] for o in p["outcomes"] for b in o["blockers"]]
    drift = [d for d in contract["drift"] if d["status"] == "open"]
    return {**result, "status": "Ready", "revision": contract["revision"], "updated_at": contract["updated_at"],
            "project_name": contract["project"]["name"], "identity": contract["project"]["identity"],
            "audience": contract["project"]["audience"], "open_blockers": len(blockers), "open_drift": len(drift),
            "open_blocker_items": blockers, "open_drift_items": drift}


def _nodes(repo: Path) -> tuple[list, list, list, str]:
    from project_compass import ContractError, validate_contract, validate_registry
    errors, links = [], []
    entries = [{"id": "project", "path": "contract.json", "kind": "root", "parent_id": None, "status": "active"}]
    root_id = "project"
    registry_path = ".project-compass/compasses.json"
    if (repo / registry_path).exists():
        try:
            registry = read_json(repo, registry_path)
            entries = registry.get("compasses", entries)
            links = registry.get("links", [])
            root_id = registry.get("root_id", "project")
            validate_registry(registry)
        except (OSError, ValueError, ContractError, AttributeError, TypeError) as exc:
            errors.append({"scope": "registry", "message": str(exc), "ref": registry_path})
    nodes = []
    if not isinstance(entries, list) or len(entries) > 500:
        entries = []
        errors.append({"scope": "registry", "message": "invalid or oversized registry"})
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            errors.append({"scope": "registry", "message": "invalid registry entry"})
            continue
        node = {**entry, "valid": False, "authority": "draft" if entry.get("status") == "draft" else "legacy-declared",
                "source_ref": ".project-compass/" + str(entry.get("path", "")), "revision": None,
                "contract_digest": None, "purpose": None, "constraints": [], "paths": [], "outcomes": []}
        try:
            contract = read_json(repo, node["source_ref"])
            validate_contract(contract)
            scope = contract.get("scope", {})
            if entry.get("kind") == "subsystem" and any(scope.get(k) != entry.get(k) for k in ("id", "kind", "parent_id")):
                raise ValueError("child scope does not match registry")
            if entry.get("id") == root_id and entry.get("path") != "contract.json":
                raise ValueError("root must be contract.json")
            node.update(valid=True, revision=contract["revision"], contract_digest=digest(contract),
                        purpose=scope.get("purpose", contract["project"]["identity"]),
                        constraints=["Excluded: " + item for item in scope.get("non_goals", contract["project"]["not_this"])],
                        paths=scope.get("paths", []),
                        outcomes=[{"id": o["id"], "name": o["name"], "intended": o["layers"]["intended"]}
                                  for p in contract["pillars"] for o in p["outcomes"]],
                        parent_outcomes=scope.get("parent_outcomes", []), summary=root_summary(contract))
        except (OSError, ValueError, ContractError, KeyError, TypeError) as exc:
            node["error"] = str(exc)
        nodes.append(node)
    by_id = {n.get("id"): n for n in nodes}
    for node in nodes:
        if node.get("kind") == "subsystem" and node["valid"]:
            parent = by_id.get(node.get("parent_id"), {})
            if not parent.get("valid") or not set(node["parent_outcomes"]).issubset({o["id"] for o in parent.get("outcomes", [])}):
                node.update(valid=False, error="missing/invalid parent or unknown parent outcome")
    if not isinstance(links, list) or len(links) > 1000:
        errors.append({"scope": "registry", "message": "invalid or oversized relationships"})
        links = []
    links = [{**l, "valid": l.get("from") in by_id and l.get("to") in by_id} for l in links if isinstance(l, dict)]
    return nodes, links, errors, root_id


def _coverage(repo: Path, development: dict, nodes: list) -> dict:
    inventory = development.get("inventory")
    result = {"status": "unknown", "unmapped_paths": [], "ambiguous_paths": [], "proposed_paths": [],
              "covered_paths": [], "excluded_paths": [], "generated_paths": [], "missing_paths": [],
              "missing_references": [], "unmapped_behaviors": []}
    by_id = {n.get("id"): n for n in nodes}
    rows = development.get("bindings", [])
    for row in rows:
        for path in row.get("paths", []):
            if not (repo / path).exists():
                result["missing_paths"].append({"path": path, "binding": row["id"]})
        for ref in row.get("references", []):
            evidence = reference(repo, ref)
            if evidence["status"] != "present":
                result["missing_references"].append({"binding": row["id"], **evidence})
    if inventory is None:
        return result
    try:
        paths = [p for p in git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0") if p]
        selected = sorted({p for p in paths if any(fnmatchcase(p, g) for g in inventory["include"])})
        for path in selected:
            exclusion = next((e for e in inventory.get("exclude", []) if fnmatchcase(path, e["pattern"])), None)
            if exclusion:
                result[exclusion["kind"] + "_paths"].append({"path": path, "reason": exclusion["reason"]})
                continue
            # Exact authored paths only: no prefix, folder, or renamed-path fallback coverage.
            owners = [r for r in rows if path in r.get("paths", [])]
            accepted = [r for r in owners if r["authority"] == "accepted" and by_id.get(r["compass_id"], {}).get("valid")
                        and by_id[r["compass_id"]].get("status") == "active"]
            key = "ambiguous_paths" if len({r["compass_id"] for r in owners}) > 1 else (
                "covered_paths" if accepted else "proposed_paths" if owners else "unmapped_paths")
            result[key].append(path)
        behavior_ref = inventory.get("behavior_ref")
        if behavior_ref:
            document = read_json(repo, behavior_ref)
            declared = {b["id"] for b in document["behaviors"]}
            mapped = {b for r in rows if r["authority"] == "accepted"
                      and by_id.get(r["compass_id"], {}).get("valid")
                      and by_id.get(r["compass_id"], {}).get("status") == "active" for b in r.get("behavior_ids", [])}
            result["unmapped_behaviors"] = sorted(declared - mapped)
            result["missing_behavior_ids"] = sorted({b for r in rows for b in r.get("behavior_ids", [])} - declared)
        result["status"] = "measured"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result.update(status="unknown", error=str(exc))
    return result


def family_projection(repo: Path) -> dict:
    from project_compass import ContractError, continuity_status, load_continuity
    repo = repo.resolve()
    nodes, links, errors, root_id = _nodes(repo)
    try:
        development = bindings(repo)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append({"scope": "development", "message": str(exc), "ref": ".project-compass/development.json"})
        development = {"status": "invalid", "bindings": [], "inventory": None}
    continuity = {"status": "missing", "active_commitments": [], "pending_reconciliations": []}
    if (repo / ".project-compass/continuity.json").exists():
        try:
            continuity = {"status": "present", **continuity_status(load_continuity(repo))}
        except (OSError, ValueError, ContractError) as exc:
            continuity.update(status="invalid", error=str(exc))
            errors.append({"scope": "continuity", "message": str(exc)})
    root = next((n for n in nodes if n.get("id") == root_id), {})
    for row in development.get("bindings", []):
        node = next((n for n in nodes if n.get("id") == row["compass_id"]), None)
        if node is None or not set(row.get("outcomes", [])).issubset({o["id"] for o in node.get("outcomes", [])}):
            errors.append({"scope": row["compass_id"], "message": f"binding {row['id']} references missing compass/outcome"})
    for node in nodes:
        if node["valid"] and node.get("status") == "active" and any(
                r["compass_id"] == node.get("id") and r["authority"] == "accepted" for r in development.get("bindings", [])):
            node["authority"] = "accepted-bindings"
    sources = {}
    for ref in [n["source_ref"] for n in nodes] + [".project-compass/" + name for name in ("compasses.json", "development.json", "continuity.json")]:
        try:
            sources[ref] = file_digest(repo, ref)
        except (OSError, ValueError) as exc:
            errors.append({"scope": "sources", "message": str(exc), "ref": ref})
    return {"schema": SCHEMA, "producer": "project-compass-python/1", "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": source_identity(repo), "source_digests": sources, "root_id": root_id,
            "root_summary": root.get("summary", root_summary(None, root.get("error"))),
            "nodes": nodes, "relationships": links, "continuity": continuity,
            "coverage": _coverage(repo, development, nodes), "development_status": development["status"],
            "errors": errors, "status": "partial" if errors or any(not n["valid"] for n in nodes) else "current",
            "verification": "Declared maturity is not current proof; use change-context evidence checks."}
