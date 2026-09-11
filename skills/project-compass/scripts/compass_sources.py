"""Bounded repository reads and versioned development bindings for Compass."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

MAX_BYTES = 1_048_576
MAX_DIGEST_BYTES = 16 * MAX_BYTES
DIGEST_CHUNK_BYTES = 65_536


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def local_path(repo: Path, name: str) -> Path:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"unsafe repository reference: {name}")
    result = (repo / name).resolve()
    if not result.is_relative_to(repo.resolve()):
        raise ValueError(f"reference escapes repository: {name}")
    return result


def read_json(repo: Path, name: str) -> Any:
    path = local_path(repo, name)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"source exceeds {MAX_BYTES} bytes: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def file_digest(repo: Path, name: str) -> str | None:
    path = local_path(repo, name)
    if not path.is_file():
        return None
    if path.stat().st_size > MAX_DIGEST_BYTES:
        raise ValueError(f"digest source exceeds {MAX_DIGEST_BYTES} bytes: {name}")
    result, consumed = hashlib.sha256(), 0
    with path.open("rb") as source:
        while chunk := source.read(DIGEST_CHUNK_BYTES):
            consumed += len(chunk)
            if consumed > MAX_DIGEST_BYTES:
                raise ValueError(f"digest source exceeds {MAX_DIGEST_BYTES} bytes: {name}")
            result.update(chunk)
    return result.hexdigest()


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=15)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip())
    if len(result.stdout) > 8 * MAX_BYTES:
        raise ValueError("Git inventory exceeds bounded projection capacity")
    return result.stdout.decode("utf-8", errors="strict")


def source_identity(repo: Path) -> dict:
    try:
        return {"workspace": str(repo.resolve()), "head": git(repo, "rev-parse", "HEAD").strip(),
                "repository": git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()}
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        return {"workspace": str(repo.resolve()), "head": None, "repository": None, "error": str(exc)}


def reference(repo: Path, ref: str) -> dict:
    """Local file or JSON Pointer; remote references are explicitly unverified."""
    if "://" in ref or ref.startswith(("conversation:", "thread:")):
        return {"ref": ref, "status": "unverified", "digest": None}
    name, _, pointer = ref.partition("#")
    try:
        value = file_digest(repo, name)
        if value is None:
            return {"ref": ref, "status": "missing", "digest": None}
        if pointer:
            if not pointer.startswith("/"):
                return {"ref": ref, "status": "unverified", "digest": value}
            target = read_json(repo, name)
            for part in pointer[1:].split("/"):
                key = part.replace("~1", "/").replace("~0", "~")
                target = target[int(key)] if isinstance(target, list) else target[key]
            value = digest(target)
        return {"ref": ref, "status": "present", "digest": value}
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        return {"ref": ref, "status": "invalid", "digest": None, "error": str(exc)}


def bindings(repo: Path) -> dict:
    name = ".project-compass/development.json"
    if not local_path(repo, name).exists():
        return {"schema": "compass-development/v1", "revision": 0, "inventory": None,
                "bindings": [], "decisions": [], "status": "missing"}
    data = read_json(repo, name)
    if not isinstance(data, dict) or data.get("schema") != "compass-development/v1":
        raise ValueError("unsupported development bindings schema")
    if type(data.get("revision")) is not int or data["revision"] < 1:
        raise ValueError("development revision must be a positive integer")
    if data.get("preservation") not in (None, "compass-preservation/v1"):
        raise ValueError("unsupported preservation contract")
    rows = data.get("bindings")
    if not isinstance(rows, list) or len(rows) > 500:
        raise ValueError("development bindings must be a bounded array")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or row["id"] in ids:
            raise ValueError("binding IDs must be unique strings")
        ids.add(row["id"])
        if row.get("authority") not in {"accepted", "proposed", "observed"}:
            raise ValueError(f"binding {row['id']} must distinguish accepted, proposed, or observed authority")
        for key in ("compass_id",):
            if not isinstance(row.get(key), str) or not row[key]:
                raise ValueError(f"binding {row['id']} requires {key}")
        for key in ("paths", "outcomes", "references", "behavior_ids", "constraints", "proof"):
            if not isinstance(row.get(key, []), list):
                raise ValueError(f"binding {row['id']}.{key} must be an array")
        for key in ("paths", "outcomes", "references", "behavior_ids", "constraints", "dependencies"):
            values = row.get(key, [])
            if not isinstance(values, list) or len(values) > 1000 or any(not isinstance(v, str) or not v for v in values):
                raise ValueError(f"binding {row['id']}.{key} requires bounded nonempty strings")
        for path in row.get("paths", []):
            local_path(repo, path)
        if "handoff_review" in row and (not isinstance(row["handoff_review"], str) or not row["handoff_review"].strip()):
            raise ValueError("handoff_review must explain the reviewed boundary")
        proof_ids = set()
        for proof in row.get("proof", []):
            if not isinstance(proof, dict) or not all(isinstance(proof.get(k), str) and proof[k] for k in ("id", "receipt")):
                raise ValueError(f"binding {row['id']} requires proof id and receipt reference")
            if proof["id"] in proof_ids:
                raise ValueError("duplicate proof ID")
            proof_ids.add(proof["id"])
            if (not isinstance(proof.get("behavior_ids", []), list)
                    or any(not isinstance(b, str) or b not in row.get("behavior_ids", []) for b in proof.get("behavior_ids", []))):
                raise ValueError("proof behavior IDs must belong to its binding")
            if not isinstance(proof.get("command"), list) or not proof["command"] or any(not isinstance(v, str) for v in proof["command"]):
                raise ValueError(f"proof {proof['id']} requires an explicit reviewed command argv")
            if not isinstance(proof.get("oracle_ref"), str) or not proof["oracle_ref"]:
                raise ValueError(f"proof {proof['id']} requires a canonical oracle reference")
    decisions = data.get("decisions", [])
    if not isinstance(decisions, list) or len(decisions) > 500:
        raise ValueError("decisions must be a bounded array")
    decision_ids = set()
    for decision in decisions:
        if (not isinstance(decision, dict) or not isinstance(decision.get("id"), str) or not decision["id"] or decision["id"] in decision_ids
                or decision.get("status") not in {"accepted", "proposed", "superseded"}
                or not isinstance(decision.get("source"), str) or not decision["source"]
                or not isinstance(decision.get("summary"), str) or not decision["summary"]):
            raise ValueError("decisions require unique IDs, status, summary, and source provenance")
        decision_ids.add(decision["id"])
        if "reasoning" in decision:
            from compass_review import validate_reasoning
            validate_reasoning(decision["reasoning"])
    for decision in decisions:
        if decision.get("supersedes") and decision["supersedes"] not in decision_ids:
            raise ValueError("decision supersedes an unknown decision")
    by_id = {d["id"]: d for d in decisions}
    for decision in decisions:
        seen, current = set(), decision
        while current.get("supersedes"):
            if current["id"] in seen:
                raise ValueError("decision supersession cycle")
            seen.add(current["id"])
            current = by_id[current["supersedes"]]
        if decision.get("supersedes") and by_id[decision["supersedes"]]["status"] != "superseded":
            raise ValueError("superseded decision must be explicitly retired")
    accepted = {d["id"] for d in decisions if d["status"] == "accepted"}
    for row in rows:
        if row["authority"] == "accepted" and row.get("decision_id") not in accepted:
            raise ValueError(f"accepted binding {row['id']} requires an accepted decision")
    inventory = data.get("inventory")
    if inventory is not None:
        if not isinstance(inventory, dict):
            raise ValueError("inventory must be an object")
        if inventory.get("source") != "git-tracked" or not isinstance(inventory.get("include"), list):
            raise ValueError("inventory requires git-tracked source and explicit include patterns")
        if any(not isinstance(p, str) or not p for p in inventory["include"]):
            raise ValueError("inventory include patterns must be nonempty strings")
        if not isinstance(inventory.get("exclude", []), list):
            raise ValueError("inventory exclusions must be an array")
        for exclusion in inventory.get("exclude", []):
            if not isinstance(exclusion, dict) or not exclusion.get("pattern") or not exclusion.get("reason") or exclusion.get("kind") not in {"generated", "excluded"}:
                raise ValueError("inventory exclusions require pattern, reason, and kind")
    return {**data, "status": "present"}
