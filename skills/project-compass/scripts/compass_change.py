"""Affected-scope preparation, completion checks, and source-bound proof."""
from __future__ import annotations

import json
import subprocess
import hashlib
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from fnmatch import fnmatchcase

from compass_projection import family_projection
from compass_bootstrap import behavior_inventory
from compass_sources import bindings, digest, git, local_path, read_json, reference, source_identity


def diff_paths(repo: Path, base: str) -> list[str]:
    revision = git(repo, "rev-parse", "--verify", base + "^{commit}").strip()
    # No rename collapsing: both removed and introduced paths must be assessed.
    changed = git(repo, "diff", "--name-only", "--no-renames", "-z", revision, "--").split("\0")
    untracked = git(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    return sorted({p for p in changed + untracked if p and not p.startswith(".project-compass/evidence/")})


def binding_inputs(repo: Path, row: dict, nodes: dict) -> dict:
    refs = sorted(set(row.get("paths", []) + row.get("references", []) + row.get("dependencies", [])
                      + [p["oracle_ref"] for p in row.get("proof", [])]))
    node = nodes.get(row["compass_id"], {})
    contracts = {}
    visited = set()
    while node and node.get("id") not in visited:
        visited.add(node["id"])
        contracts[node["id"]] = node.get("contract_digest")
        node = nodes.get(node.get("parent_id"), {})
    development = bindings(repo)
    behavior = behavior_inventory(repo, development.get("inventory"))
    relevant_behaviors = [b for b in behavior["behaviors"] if b["id"] in row.get("behavior_ids", [])]
    refs = sorted(set(refs + [b["spec_ref"] for b in relevant_behaviors if isinstance(b.get("spec_ref"), str)]))
    decision = next((d for d in development.get("decisions", []) if d["id"] == row.get("decision_id")), None)
    registry_path = repo / ".project-compass/compasses.json"
    links = read_json(repo, ".project-compass/compasses.json").get("links", []) if registry_path.exists() else []
    links = [l for l in links if row["compass_id"] in (l.get("from"), l.get("to"))]
    return {"behavior_contracts": digest(relevant_behaviors), "binding": digest(row), "decision": digest(decision), "relationships": digest(links), "contracts": contracts,
            "commitments": digest(scoped_commitments(family_projection(repo)["continuity"], set(contracts))),
            "references": {ref: reference(repo, ref) for ref in refs}}


def scoped_commitments(continuity: dict, scopes: set) -> list:
    # Historical unscoped commitments remain global; scope never comes from prose.
    return [c for c in continuity.get("active_commitments", [])
            if not c.get("compass_ids") or scopes.intersection(c["compass_ids"])]


def proof_status(repo: Path, row: dict, requirement: dict, nodes: dict) -> dict:
    result = {"id": requirement["id"], "binding": row["id"], "receipt": requirement["receipt"], "status": "missing"}
    try:
        receipt = read_json(repo, requirement["receipt"])
        if receipt.get("schema") != "compass-evidence/v1" or receipt.get("producer") != "project-compass-check/v1":
            return {**result, "status": "unsupported"}
        current = binding_inputs(repo, row, nodes)
        if (receipt.get("inputs") != current or receipt.get("workspace") != str(repo.resolve())
                or receipt.get("repository") != source_identity(repo).get("repository")
                or receipt.get("requirement_id") != requirement["id"] or receipt.get("command") != requirement["command"]):
            return {**result, "status": "stale"}
        return {**result, "status": "current" if receipt.get("exit_code") == 0 else "failed",
                "observed_at": receipt.get("observed_at"), "command": receipt.get("command")}
    except FileNotFoundError:
        return result
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return {**result, "status": "invalid", "error": str(exc)}


def change_context(repo: Path, *, paths: list[str], compass_ids: list[str], base: str,
                   prepared: dict | None = None, completion: bool = False, continuation: bool = False) -> dict:
    if prepared is not None and not isinstance(prepared, dict):
        raise ValueError("prepared context must be an object")
    if continuation and (prepared is None or completion):
        raise ValueError("continuation requires the prior packet at task entry")
    repo = repo.resolve()
    family = family_projection(repo)
    development = bindings(repo)
    nodes = {n.get("id"): n for n in family["nodes"]}
    rows = development.get("bindings", [])
    inventory = behavior_inventory(repo, development.get("inventory"))
    behaviors = {b["id"]: b for b in inventory["behaviors"]}
    def behavior_refs(row):
        return [b["spec_ref"] for name in row.get("behavior_ids", []) if (b := behaviors.get(name)) and isinstance(b.get("spec_ref"), str)]
    base_sha = git(repo, "rev-parse", "--verify", base + "^{commit}").strip()
    selected = sorted(set(diff_paths(repo, base_sha) if completion else paths))
    if continuation:
        selected = sorted(set(selected + prepared.get("selected_paths", [])))
        compass_ids = sorted(set(compass_ids + prepared.get("direct_compasses", [])))
    for path in selected:
        local_path(repo, path)
    if not selected and not compass_ids:
        raise ValueError("select paths or compass IDs; completion requires an actual diff")
    affected = set(compass_ids)
    blockers, unknowns = [], []
    for path in selected:
        excluded = next((e for e in (development.get("inventory") or {}).get("exclude", [])
                         if fnmatchcase(path, e["pattern"])), None)
        if excluded:
            unknowns.append({"kind": excluded["kind"] + "-path", "path": path, "reason": excluded["reason"]})
        owners = {r["compass_id"] for r in rows if path in r.get("paths", []) + r.get("dependencies", [])
                  or any(ref.split("#")[0] == path for ref in r.get("references", []) + behavior_refs(r)
                         + [p["oracle_ref"] for p in r.get("proof", [])])
                  or (path == (development.get("inventory") or {}).get("behavior_ref") and r.get("behavior_ids"))}
        affected.update(owners)
        if not owners and not excluded:
            blockers.append({"kind": "unmapped-path", "path": path})
        elif len(owners) > 1:
            unknowns.append({"kind": "shared-ownership", "path": path, "compasses": sorted(owners)})
    direct = set(affected)
    # Consumer closure includes transitive handoffs and shared interfaces.
    while True:
        previous = set(affected)
        for link in family["relationships"]:
            if link.get("to") in affected or (link.get("kind") == "shared-invariant" and link.get("from") in affected):
                affected.update((link.get("from"), link.get("to")))
        if previous == affected:
            break
    impact = set(affected)
    for name in list(affected):
        visited = set()
        parent = nodes.get(name, {}).get("parent_id")
        while parent and parent not in visited:
            visited.add(parent)
            affected.add(parent)
            parent = nodes.get(parent, {}).get("parent_id")
    affected.add(family["root_id"])
    relevant = [r for r in rows if r["compass_id"] in affected]
    proofs = []
    relationships = [l for l in family["relationships"] if l.get("from") in impact or l.get("to") in impact]
    bootstrap = []
    for assessment in family["bootstrap"]["subsystems"]:
        if assessment["compass_id"] not in affected:
            continue
        gaps = list(assessment["gaps"])
        if "handoff-unresolved" in gaps and not any(
                assessment["compass_id"] in (link.get("from"), link.get("to"))
                and (not link.get("valid") or link.get("status") != "aligned") for link in relationships):
            gaps.remove("handoff-unresolved")
        bootstrap.append({**assessment, "gaps": gaps, "status": "incomplete" if gaps else "linked"})
    for assessment in bootstrap:
        if assessment["status"] != "linked":
            finding = {"kind": "bootstrap-incomplete", "compass_id": assessment["compass_id"], "gaps": assessment["gaps"]}
            (blockers if development.get("preservation") == "compass-preservation/v1" else unknowns).append(finding)
    for name in sorted(affected):
        node = nodes.get(name)
        if node is None or not node.get("valid"):
            blockers.append({"kind": "invalid-compass", "compass_id": name})
        elif node.get("status") != "active":
            blockers.append({"kind": "unaccepted-compass", "compass_id": name, "status": node.get("status")})
        if not any(r["compass_id"] == name and r["authority"] == "accepted" for r in relevant):
            blockers.append({"kind": "intent-unreconciled", "compass_id": name})
    for row in relevant:
        if row["authority"] != "accepted":
            unknowns.append({"kind": row["authority"] + "-binding", "binding": row["id"]})
            if row["authority"] == "proposed" and (set(selected).intersection(row.get("paths", [])) or row["compass_id"] in compass_ids):
                blockers.append({"kind": "intent-proposal-unreconciled", "binding": row["id"]})
            continue
        if not row.get("proof"):
            blockers.append({"kind": "proof-undeclared", "binding": row["id"]})
        for ref in row.get("references", []) + row.get("dependencies", []):
            state = reference(repo, ref)
            if state["status"] != "present":
                blockers.append({"kind": "missing-reference", "binding": row["id"], **state})
        if row.get("behavior_ids"):
            inventory = development.get("inventory") or {}
            behavior_ref = inventory.get("behavior_ref")
            try:
                declared = {b["id"] for b in read_json(repo, behavior_ref)["behaviors"]} if behavior_ref else set()
                missing = sorted(set(row["behavior_ids"]) - declared)
                if missing:
                    blockers.append({"kind": "missing-behavior-reference", "binding": row["id"], "behavior_ids": missing})
            except (OSError, ValueError, TypeError, KeyError) as exc:
                blockers.append({"kind": "behavior-inventory-invalid", "binding": row["id"], "error": str(exc)})
        for requirement in row.get("proof", []):
            proof = proof_status(repo, row, requirement, nodes)
            proofs.append(proof)
            if completion and proof["status"] != "current":
                blockers.append({"kind": "required-proof", **proof})
    relationships = [l for l in family["relationships"] if l.get("from") in impact or l.get("to") in impact]
    for link in relationships:
        if not link["valid"] or link.get("status") != "aligned":
            blockers.append({"kind": "unresolved-relationship", "id": link.get("id"), "status": link.get("status")})
    continuity = family["continuity"]
    commitments = scoped_commitments(continuity, affected)
    commitment_revisions = {c["id"]: digest(c) for c in commitments}
    for commitment in commitments:
        if commitment.get("status") == "unresolved":
            blockers.append({"kind": "continuity-commitment-unresolved", "id": commitment["id"]})
    for reconciliation in continuity.get("pending_reconciliations", []):
        # Unscoped historical commitments are global; never infer them unrelated.
        scopes = reconciliation.get("compass_ids", [family["root_id"]])
        if affected.intersection(scopes):
            blockers.append({"kind": "continuity-conflict", "id": reconciliation.get("id")})
    for error in family["errors"]:
        if error["scope"] in affected or error["scope"] in {"registry", "development", "continuity", "sources"}:
            blockers.append({"kind": "source-invalid", **error})
    revisions = {name: nodes[name]["contract_digest"] for name in sorted(affected) if name in nodes}
    binding_revisions = {r["id"]: digest(r) for r in relevant if r["authority"] == "accepted"}
    decision_revisions = {d["id"]: digest(d) for d in development.get("decisions", [])
                          if d["id"] in {r.get("decision_id") for r in relevant}}
    behavior_revisions = {name: digest({"behavior": behaviors.get(name), "specification": reference(repo, behaviors[name]["spec_ref"])
                          if name in behaviors and isinstance(behaviors[name].get("spec_ref"), str) else None})
                          for name in {b for r in relevant for b in r.get("behavior_ids", [])}}
    relationship_revision = digest(relationships)
    if completion and prepared is None:
        blockers.append({"kind": "prepared-context-required"})
    if prepared is not None:
        if prepared.get("eligible") is not True:
            blockers.append({"kind": "prepared-context-ineligible", "action": "Reconcile using the last eligible packet; a failed assessment cannot become the baseline."})
        if prepared.get("schema") != "compass-change-context/v1" or prepared.get("source", {}).get("workspace") != str(repo):
            blockers.append({"kind": "prepared-context-mismatch"})
        if prepared.get("base_revision") != base_sha:
            blockers.append({"kind": "base-revision-changed"})
        expansion = sorted(set(selected) - set(prepared.get("selected_paths", [])))
        if expansion and not continuation:
            blockers.append({"kind": "scope-expanded", "paths": expansion})
        def revision_changed(key, current):
            previous = prepared.get(key)
            return (not isinstance(previous, dict) or any(current.get(k) != v for k, v in previous.items())) if continuation else previous != current
        if (prepared.get("preservation", {}).get("mode", "legacy-advisory") != development.get("preservation", "legacy-advisory")
                or revision_changed("commitment_revisions", commitment_revisions)
                or revision_changed("behavior_revisions", behavior_revisions)
                or revision_changed("contract_revisions", revisions) or revision_changed("binding_revisions", binding_revisions)
                or revision_changed("decision_revisions", decision_revisions)
                or (not continuation and prepared.get("relationship_revision") != relationship_revision)
                or (continuation and any(link not in relationships for link in prepared.get("relationships", [])))):
            blockers.append({"kind": "intent-revision-changed", "action": "Reconcile against current decisions and prepare a new packet."})
    return {"schema": "compass-change-context/v1", "source": source_identity(repo), "base_revision": base_sha,
            "phase": "completion" if completion else "entry",
            "preservation": {"schema": "compass-preservation-context/v1",
                             "mode": development.get("preservation", "legacy-advisory"),
                             "parent_packet_digest": digest(prepared) if continuation else None,
                             "bootstrap": bootstrap,
                             "instruction": "Keep this original base and cumulative scope across milestones; continue from the prior packet. Review semantic preservation against linked behavior oracles."}, "selected_paths": selected,
            "affected_compasses": sorted(affected), "direct_compasses": sorted(direct),
            "contract_revisions": revisions, "binding_revisions": binding_revisions,
            "decision_revisions": decision_revisions, "behavior_revisions": behavior_revisions,
            "commitment_revisions": commitment_revisions, "commitments": commitments, "relationship_revision": relationship_revision,
            "contracts": [{k: n.get(k) for k in ("id", "purpose", "authority", "status", "constraints", "outcomes", "source_ref")}
                          for name in sorted(affected) if (n := nodes.get(name))],
            "bindings": [{k: r.get(k, []) for k in ("id", "compass_id", "authority", "outcomes", "constraints", "references", "dependencies", "behavior_ids", "decision_id")}
                         for r in relevant],
            "decisions": [d for d in development.get("decisions", []) if d["id"] in decision_revisions],
            "relationships": relationships, "required_proof": proofs, "blockers": blockers, "unknowns": unknowns,
            "eligible": not blockers, "execution_authority": False,
            "drill_down": {"family": "family --json", "development": ".project-compass/development.json"},
            "unrelated_family_gaps": (sum(1 for n in family["nodes"] if n.get("id") not in affected
                                           and (not n["valid"] or n.get("authority") != "accepted-bindings"))
                                      + sum(1 for link in family["relationships"] if link not in relationships
                                            and (not link["valid"] or link.get("status") != "aligned")))}


def prove(repo: Path, binding_id: str, proof_id: str, command: list[str]) -> dict:
    """Execute only the explicitly supplied validation argv; contracts never execute code."""
    if not command:
        raise ValueError("proof requires an explicit validation command after --")
    family = family_projection(repo)
    nodes = {n.get("id"): n for n in family["nodes"]}
    row = next((r for r in bindings(repo)["bindings"] if r["id"] == binding_id), None)
    if row is None:
        raise ValueError("unknown binding")
    requirement = next((p for p in row.get("proof", []) if p["id"] == proof_id), None)
    if requirement is None:
        raise ValueError("unknown proof requirement")
    if command != requirement["command"]:
        raise ValueError("validation argv differs from the reviewed proof requirement")
    destination = requirement["receipt"]
    if not destination.startswith(".project-compass/evidence/"):
        raise ValueError("proof receipts must stay in .project-compass/evidence/")
    before = binding_inputs(repo, row, nodes)
    if any(v["status"] != "present" for v in before["references"].values()):
        raise ValueError("proof dependencies must exist and be locally verifiable")
    # Spool output instead of retaining arbitrary test output in memory.
    with tempfile.TemporaryFile() as output:
        result = subprocess.run(command, cwd=repo, stdout=output, stderr=subprocess.STDOUT, timeout=120)
        output.seek(0)
        output_digest = hashlib.file_digest(output, "sha256").hexdigest()
    after_family = family_projection(repo)
    after_rows = bindings(repo)["bindings"]
    after_row = next((r for r in after_rows if r["id"] == binding_id), {})
    if not after_row:
        raise ValueError("sources changed during verification; binding removed")
    after = binding_inputs(repo, after_row, {n.get("id"): n for n in after_family["nodes"]})
    if before != after:
        raise ValueError("sources changed during verification; proof not recorded")
    receipt = {"schema": "compass-evidence/v1", "producer": "project-compass-check/v1",
               "workspace": str(repo.resolve()), "repository": source_identity(repo).get("repository"), "requirement_id": proof_id, "inputs": before,
               "observed_at": datetime.now(timezone.utc).isoformat(), "command": command,
               "exit_code": result.returncode, "output_digest": output_digest}
    path = local_path(repo, destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as output:
        output.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        temporary = Path(output.name)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return {"receipt": destination, "exit_code": result.returncode, "recorded": True}
