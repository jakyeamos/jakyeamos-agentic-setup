#!/usr/bin/env python3
"""Scoped-compass and intent-quiz behavior used by the public helper."""

from __future__ import annotations

import json
import hashlib
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COMPASS_KINDS = {"root", "subsystem"}
COMPASS_STATUSES = {"active", "draft", "retired"}
LINK_KINDS = {"depends-on", "handoff", "shared-invariant"}
LINK_STATUSES = {"aligned", "unknown", "blocked", "drift"}
QUIZ_MODES = {"greenfield", "brownfield", "realignment"}
QUIZ_STATUSES = {"active", "complete", "abandoned"}
QUIZ_ANSWER_STATUSES = {"explicit", "tentative", "unknown", "skipped"}

_DEPENDENCIES: dict[str, Any] = {}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def configure(**dependencies: Any) -> None:
    """Bind the stable contract/scoring primitives owned by the entrypoint."""
    _DEPENDENCIES.clear()
    _DEPENDENCIES.update(dependencies)


def _dependency(name: str) -> Any:
    if name not in _DEPENDENCIES:
        raise RuntimeError(f"Project Compass extension dependency is unbound: {name}")
    return _DEPENDENCIES[name]


def _require(condition: bool, message: str) -> None:
    _dependency("require")(condition, message)


def _validate_timestamp(value: Any, path: str) -> None:
    _dependency("validate_timestamp")(value, path)


def _validate_source(value: Any, path: str) -> None:
    _dependency("validate_source")(value, path)


def _validate_relative_path(value: Any, path: str) -> None:
    _dependency("validate_relative_path")(value, path)


def _contract_error(message: str) -> Exception:
    return _dependency("contract_error")(message)


def validate_registry(data: dict[str, Any]) -> None:
    _require(isinstance(data, dict), "registry root must be an object")
    _require(data.get("schema_version") == 1,
             "registry.schema_version must be 1")
    root_id = data.get("root_id")
    _require(isinstance(root_id, str) and ID_PATTERN.fullmatch(root_id),
             "registry.root_id must be hyphen-case")

    entries = data.get("compasses")
    _require(isinstance(entries, list) and entries,
             "registry.compasses must be a non-empty array")
    compass_ids: set[str] = set()
    paths: set[str] = set()
    root_entries: list[dict[str, Any]] = []
    parents: dict[str, str | None] = {}
    for index, entry in enumerate(entries):
        prefix = f"registry.compasses[{index}]"
        _require(isinstance(entry, dict), f"{prefix} must be an object")
        compass_id = entry.get("id")
        _require(isinstance(compass_id, str) and ID_PATTERN.fullmatch(compass_id),
                 f"{prefix}.id must be hyphen-case")
        _require(compass_id not in compass_ids,
                 f"duplicate compass id: {compass_id}")
        compass_ids.add(compass_id)
        kind = entry.get("kind")
        _require(kind in COMPASS_KINDS, f"{prefix}.kind is invalid")
        artifact_path = entry.get("path")
        _validate_relative_path(artifact_path, f"{prefix}.path")
        _require(artifact_path not in paths,
                 f"duplicate compass path: {artifact_path}")
        paths.add(artifact_path)
        parent_id = entry.get("parent_id")
        if kind == "root":
            _require(parent_id is None,
                     f"{prefix}.parent_id must be null for a root")
            root_entries.append(entry)
        else:
            _require(isinstance(parent_id, str)
                     and ID_PATTERN.fullmatch(parent_id),
                     f"{prefix}.parent_id must be a compass id")
            _require(parent_id != compass_id,
                     f"{prefix}.parent_id cannot reference itself")
        _require(entry.get("status") in COMPASS_STATUSES,
                 f"{prefix}.status is invalid")
        parents[compass_id] = parent_id

    _require(root_id in compass_ids,
             "registry.root_id must reference a declared compass")
    for compass_id, parent_id in parents.items():
        if parent_id is not None:
            _require(parent_id in compass_ids,
                     f"compass {compass_id} references an undeclared parent")
    _require(len(root_entries) == 1,
             "registry must declare exactly one root compass")
    _require(root_entries[0]["id"] == root_id,
             "registry.root_id must reference the root compass")

    for compass_id in compass_ids:
        visited: set[str] = set()
        current: str | None = compass_id
        while current is not None:
            _require(current not in visited,
                     f"compass parent cycle includes: {current}")
            visited.add(current)
            current = parents[current]

    links = data.get("links")
    _require(isinstance(links, list), "registry.links must be an array")
    link_ids: set[str] = set()
    for index, link in enumerate(links):
        prefix = f"registry.links[{index}]"
        _require(isinstance(link, dict), f"{prefix} must be an object")
        link_id = link.get("id")
        _require(isinstance(link_id, str) and ID_PATTERN.fullmatch(link_id),
                 f"{prefix}.id must be hyphen-case")
        _require(link_id not in link_ids, f"duplicate link id: {link_id}")
        link_ids.add(link_id)
        for field in ("from", "to"):
            endpoint = link.get(field)
            _require(endpoint in compass_ids,
                     f"{prefix}.{field} must reference a declared compass")
        _require(link["from"] != link["to"],
                 f"{prefix} cannot link a compass to itself")
        _require(link.get("kind") in LINK_KINDS,
                 f"{prefix}.kind is invalid")
        _require(link.get("status") in LINK_STATUSES,
                 f"{prefix}.status is invalid")
        _require(isinstance(link.get("summary"), str)
                 and link["summary"].strip(),
                 f"{prefix}.summary must be a non-empty string")
    _validate_timestamp(data.get("updated_at"), "registry.updated_at")


def _load_json_file(path: Path, label: str) -> dict[str, Any]:
    _require(path.is_file(), f"{label} not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _contract_error(f"cannot read {label}: {exc}") from exc
    _require(isinstance(data, dict), f"{label} root must be an object")
    return data


def load_registry(repo: Path) -> dict[str, Any]:
    data = _load_json_file(_dependency("registry_path")(repo), "compass registry")
    validate_registry(data)
    return data


def _registry_artifact_path(repo: Path, artifact_path: str) -> Path:
    base = (repo / ".project-compass").resolve()
    target = (base / artifact_path).resolve()
    _require(target != base and base in target.parents,
             f"registry path escapes .project-compass: {artifact_path}")
    return target


def _outcome_ids(contract: dict[str, Any]) -> set[str]:
    return {
        outcome["id"]
        for pillar in contract["pillars"]
        for outcome in pillar["outcomes"]
    }


def load_compass_family(repo: Path) -> dict[str, Any]:
    root = _dependency("load_contract")(repo)
    _dependency("validate_contract")(root)
    registry_path = _dependency("registry_path")(repo)
    if not registry_path.exists():
        return {
            "registry": None,
            "root_id": "project",
            "entries": [{
                "id": "project",
                "kind": "root",
                "path": "contract.json",
                "parent_id": None,
                "status": "active",
            }],
            "links": [],
            "contracts": {"project": root},
        }

    registry = load_registry(repo)
    contracts: dict[str, dict[str, Any]] = {}
    for entry in registry["compasses"]:
        compass_path = _registry_artifact_path(repo, entry["path"])
        contract = _load_json_file(compass_path, f"compass {entry['id']}")
        _dependency("validate_contract")(contract)
        scope = contract.get("scope")
        if entry["kind"] == "subsystem":
            _require(scope is not None,
                     f"compass {entry['id']} must declare scope metadata")
        if scope is not None:
            _require(scope["id"] == entry["id"],
                     f"compass {entry['id']} scope.id does not match registry")
            _require(scope["kind"] == entry["kind"],
                     f"compass {entry['id']} scope.kind does not match registry")
            _require(scope["parent_id"] == entry["parent_id"],
                     f"compass {entry['id']} scope.parent_id does not match registry")
        contracts[entry["id"]] = contract

    root_entry = next(
        entry for entry in registry["compasses"] if entry["id"] == registry["root_id"]
    )
    _require(root_entry["path"] == "contract.json",
             "the root compass must be stored at contract.json")
    _require(contracts[registry["root_id"]] == root,
             "registry root compass must match contract.json")

    for entry in registry["compasses"]:
        if entry["kind"] != "subsystem":
            continue
        parent = contracts[entry["parent_id"]]
        scope = contracts[entry["id"]]["scope"]
        _require(
            set(scope["parent_outcomes"]).issubset(_outcome_ids(parent)),
            f"compass {entry['id']} references an unknown parent outcome",
        )

    return {
        "registry": registry,
        "root_id": registry["root_id"],
        "entries": registry["compasses"],
        "links": registry["links"],
        "contracts": contracts,
    }


def validate_quiz(data: dict[str, Any]) -> None:
    _require(isinstance(data, dict), "quiz root must be an object")
    _require(data.get("schema_version") == 1,
             "quiz.schema_version must be 1")
    sessions = data.get("sessions")
    _require(isinstance(sessions, list), "quiz.sessions must be an array")
    session_ids: set[str] = set()
    for index, session in enumerate(sessions):
        prefix = f"quiz.sessions[{index}]"
        _require(isinstance(session, dict), f"{prefix} must be an object")
        session_id = session.get("id")
        _require(isinstance(session_id, str) and ID_PATTERN.fullmatch(session_id),
                 f"{prefix}.id must be hyphen-case")
        _require(session_id not in session_ids,
                 f"duplicate quiz session id: {session_id}")
        session_ids.add(session_id)
        _require(session.get("mode") in QUIZ_MODES,
                 f"{prefix}.mode is invalid")
        compass_id = session.get("compass_id")
        _require(isinstance(compass_id, str) and ID_PATTERN.fullmatch(compass_id),
                 f"{prefix}.compass_id must be hyphen-case")
        _require(session.get("scope_kind") in COMPASS_KINDS,
                 f"{prefix}.scope_kind is invalid")
        _require(session.get("status") in QUIZ_STATUSES,
                 f"{prefix}.status is invalid")
        questions = session.get("questions")
        _require(isinstance(questions, list) and questions,
                 f"{prefix}.questions must be a non-empty array")
        question_ids: set[str] = set()
        for question_index, question in enumerate(questions):
            qprefix = f"{prefix}.questions[{question_index}]"
            _require(isinstance(question, dict), f"{qprefix} must be an object")
            question_id = question.get("id")
            _require(isinstance(question_id, str)
                     and ID_PATTERN.fullmatch(question_id),
                     f"{qprefix}.id must be hyphen-case")
            _require(question_id not in question_ids,
                     f"duplicate quiz question id: {question_id}")
            question_ids.add(question_id)
            for field in ("category", "prompt"):
                _require(isinstance(question.get(field), str)
                         and question[field].strip(),
                         f"{qprefix}.{field} must be a non-empty string")
        answers = session.get("answers")
        _require(isinstance(answers, list), f"{prefix}.answers must be an array")
        for answer_index, answer in enumerate(answers):
            aprefix = f"{prefix}.answers[{answer_index}]"
            _require(isinstance(answer, dict), f"{aprefix} must be an object")
            _require(answer.get("question_id") in question_ids,
                     f"{aprefix}.question_id must reference a question")
            _require(isinstance(answer.get("value"), str)
                     and answer["value"].strip(),
                     f"{aprefix}.value must be a non-empty string")
            _require(answer.get("status") in QUIZ_ANSWER_STATUSES,
                     f"{aprefix}.status is invalid")
            _validate_source(answer.get("source"), f"{aprefix}.source")
            _validate_timestamp(answer.get("answered_at"),
                                f"{aprefix}.answered_at")
        _validate_timestamp(session.get("started_at"),
                            f"{prefix}.started_at")
        _validate_timestamp(session.get("updated_at"),
                            f"{prefix}.updated_at")
    _validate_timestamp(data.get("updated_at"), "quiz.updated_at")


def load_quiz(repo: Path) -> dict[str, Any]:
    data = _load_json_file(_dependency("quiz_path")(repo), "quiz sessions")
    validate_quiz(data)
    return data


def _alignment_summary(family: dict[str, Any]) -> dict[str, Any]:
    counts = {status: 0 for status in sorted(LINK_STATUSES)}
    unresolved: list[str] = []
    for link in family["links"]:
        counts[link["status"]] += 1
        if link["status"] != "aligned":
            unresolved.append(link["id"])
    current_children = [
        entry for entry in family["entries"]
        if entry["id"] != family["root_id"] and entry["status"] != "retired"
    ]
    linked_children = {
        endpoint
        for link in family["links"]
        for endpoint in (link["from"], link["to"])
        if endpoint != family["root_id"]
    }
    unlinked_children = sorted(
        entry["id"] for entry in current_children
        if entry["id"] not in linked_children
    )
    if any(counts[state] for state in ("blocked", "drift")):
        status = "attention"
    elif counts["unknown"] or unlinked_children:
        status = "unknown"
    else:
        status = "aligned"
    return {
        "status": status,
        "link_count": len(family["links"]),
        "link_counts": counts,
        "unresolved_links": sorted(unresolved),
        "unlinked_children": unlinked_children,
    }


def score_compass_family(repo: Path) -> dict[str, Any]:
    family = load_compass_family(repo)
    children: dict[str, Any] = {}
    for entry in family["entries"]:
        if entry["id"] == family["root_id"] or entry["status"] == "retired":
            continue
        children[entry["id"]] = {
            "kind": entry["kind"],
            "parent_id": entry["parent_id"],
            "status": entry["status"],
            "scope": family["contracts"][entry["id"]].get("scope"),
            "score": _dependency("score_contract")(
                family["contracts"][entry["id"]]
            ),
        }
    return {
        "root_id": family["root_id"],
        "root": _dependency("score_contract")(
            family["contracts"][family["root_id"]]
        ),
        "children": children,
        "alignment": _alignment_summary(family),
        "coverage": {
            "total_compasses": len(family["entries"]),
            "active_compasses": sum(
                1 for entry in family["entries"]
                if entry["status"] == "active"
            ),
            "child_compasses": len(children),
            "retired_compasses": sum(
                1 for entry in family["entries"]
                if entry["status"] == "retired"
            ),
        },
    }


def _quiz_questions(mode: str, scope_kind: str) -> list[dict[str, str]]:
    _require(mode in QUIZ_MODES, f"quiz mode is invalid: {mode}")
    _require(scope_kind in COMPASS_KINDS,
             f"quiz scope kind is invalid: {scope_kind}")
    if scope_kind == "subsystem":
        question_sets = {
            "greenfield": [
                ("purpose", "purpose", "What should this part make possible?"),
                ("parent-outcome", "alignment", "Which parent outcome does it directly advance?"),
                ("responsibilities", "boundary", "What is this part responsible for, and what is explicitly outside its job?"),
                ("interfaces", "interfaces", "What must this part receive, provide, or guarantee to neighboring parts?"),
                ("proof", "verification", "What observable result would prove this part works in its intended use?"),
            ],
            "brownfield": [
                ("desired-purpose", "purpose", "What should this part be responsible for, regardless of what the current code does?"),
                ("intentional-responsibility", "boundary", "Which current responsibilities are intentional and worth preserving?"),
                ("accidental-behavior", "drift", "Which current behaviors look historical, accidental, or unclear?"),
                ("preserve-or-redirect", "alignment", "What should be preserved, redirected, retired, or left unknown?"),
                ("interface-proof", "verification", "What handoff or observable result would prove this part is aligned?"),
            ],
            "realignment": [
                ("desired-change", "purpose", "What should this part do differently after realignment?"),
                ("preserve-invariant", "boundary", "What must remain true while this part changes?"),
                ("boundary-conflict", "drift", "Which observed behavior or boundary conflicts with the desired purpose?"),
                ("sibling-contract", "interfaces", "What must neighboring parts change or continue to guarantee?"),
                ("proof", "verification", "What evidence would prove the realignment is working in real use?"),
            ],
        }
    else:
        question_sets = {
            "greenfield": [
                ("purpose", "purpose", "What should this project make possible for a real user?"),
                ("audience", "audience", "Who is this for, and whose problem matters first?"),
                ("core-loop", "experience", "What should the user do and experience from start to finish?"),
                ("boundary", "boundary", "What must this project explicitly not become?"),
                ("finish-line", "finish-line", "What would make the first real release feel honest?"),
                ("proof", "verification", "What real-use evidence would prove the project is working?"),
            ],
            "brownfield": [
                ("desired-purpose", "purpose", "What should this project become, independent of what the current code assumes?"),
                ("intentional-behavior", "experience", "Which current behaviors are intentional and worth preserving?"),
                ("historical-drift", "drift", "Which parts look legacy, accidental, or based on a misconception?"),
                ("preserve-or-change", "boundary", "What should be preserved, redirected, retired, or left unknown?"),
                ("finish-line", "finish-line", "What would make the next honest release feel complete enough?"),
                ("proof", "verification", "What real-use evidence would prove the realignment is working?"),
            ],
            "realignment": [
                ("desired-realignment", "purpose", "What outcome should be different after realignment?"),
                ("preserve", "boundary", "What existing truth, behavior, or constraint must remain?"),
                ("contradiction", "drift", "What current behavior or plan contradicts the desired outcome?"),
                ("defer-or-retire", "scope", "What should be deferred, retired, or explicitly left behind?"),
                ("finish-line", "finish-line", "What is the smallest honest finish line for this direction?"),
                ("proof", "verification", "What evidence would prove the realignment in real use?"),
            ],
        }
    return [
        {"id": question_id, "category": category, "prompt": prompt}
        for question_id, category, prompt in question_sets[mode]
    ]


def _quiz_scope_kind(
    repo: Path,
    mode: str,
    compass_id: str,
    requested_scope_kind: str | None = None,
) -> str:
    _require(mode in QUIZ_MODES, f"quiz mode is invalid: {mode}")
    _require(
        isinstance(compass_id, str) and ID_PATTERN.fullmatch(compass_id),
        "quiz compass_id must be hyphen-case",
    )
    if requested_scope_kind is not None:
        _require(
            requested_scope_kind in COMPASS_KINDS,
            f"quiz scope kind is invalid: {requested_scope_kind}",
        )
    contract_path = _dependency("contract_path")(repo)
    if not contract_path.exists():
        _require(
            mode in {"greenfield", "brownfield"},
            "a missing contract only supports a greenfield or brownfield quiz",
        )
        if requested_scope_kind == "subsystem":
            _require(
                compass_id != "project",
                "a subsystem quiz needs a non-project compass_id",
            )
            return "subsystem"
        _require(
            compass_id == "project",
            "a root quiz without a contract must use compass_id project",
        )
        return "root"
    family = load_compass_family(repo)
    if compass_id not in family["contracts"]:
        _require(
            requested_scope_kind == "subsystem"
            and mode in {"greenfield", "brownfield"},
            f"compass not found: {compass_id}",
        )
        return "subsystem"
    entry = next(item for item in family["entries"] if item["id"] == compass_id)
    _require(
        requested_scope_kind is None or requested_scope_kind == entry["kind"],
        f"compass {compass_id} is a {entry['kind']} compass, not a {requested_scope_kind}",
    )
    return entry["kind"]


def _quiz_status(session: dict[str, Any]) -> dict[str, Any]:
    latest_answers: dict[str, dict[str, Any]] = {}
    for answer in session["answers"]:
        latest_answers[answer["question_id"]] = answer
    next_question = next(
        (
            question for question in session["questions"]
            if question["id"] not in latest_answers
        ),
        None,
    )
    return {
        "session_id": session["id"],
        "mode": session["mode"],
        "compass_id": session["compass_id"],
        "scope_kind": session["scope_kind"],
        "status": session["status"],
        "answered": len(latest_answers),
        "total_questions": len(session["questions"]),
        "next_question": next_question,
        "answer_statuses": {
            question_id: answer["status"]
            for question_id, answer in sorted(latest_answers.items())
        },
        "draft_only": True,
        "ratification": "manual-review-required",
    }


def _timestamp(value: str | None = None) -> str:
    return value or datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def start_quiz(
    repo: Path,
    mode: str,
    compass_id: str = "project",
    session_id: str | None = None,
    now: str | None = None,
    scope_kind: str | None = None,
) -> dict[str, Any]:
    started_at = _timestamp(now)
    resolved_scope_kind = _quiz_scope_kind(
        repo, mode, compass_id, requested_scope_kind=scope_kind
    )
    if session_id is None:
        suffix = datetime.fromisoformat(
            started_at.replace("Z", "+00:00")
        ).strftime("%Y%m%d%H%M%S%f")
        session_id = f"{mode}-{compass_id}-{suffix}"
    pattern = _dependency("id_pattern")
    _require(pattern.fullmatch(session_id) is not None,
             "quiz session_id must be hyphen-case")
    quiz_path = _dependency("quiz_path")(repo)
    if quiz_path.exists():
        quiz = load_quiz(repo)
    else:
        quiz = {
            "schema_version": 1,
            "sessions": [],
            "updated_at": started_at,
        }
    _require(
        all(session["id"] != session_id for session in quiz["sessions"]),
        f"quiz session already exists: {session_id}",
    )
    session = {
        "id": session_id,
        "mode": mode,
        "compass_id": compass_id,
        "scope_kind": resolved_scope_kind,
        "status": "active",
        "questions": _quiz_questions(mode, resolved_scope_kind),
        "answers": [],
        "started_at": started_at,
        "updated_at": started_at,
    }
    quiz["sessions"].append(session)
    quiz["updated_at"] = started_at
    validate_quiz(quiz)
    _atomic_write_json(quiz_path, quiz)
    return _quiz_status(session)


def answer_quiz(
    repo: Path,
    session_id: str,
    question_id: str,
    value: str,
    status: str = "explicit",
    source_ref: str = "conversation:user",
    now: str | None = None,
) -> dict[str, Any]:
    quiz = load_quiz(repo)
    session = next(
        (item for item in quiz["sessions"] if item["id"] == session_id),
        None,
    )
    _require(session is not None, f"quiz session not found: {session_id}")
    _require(session["status"] == "active",
             f"quiz session is not active: {session_id}")
    _require(status in QUIZ_ANSWER_STATUSES,
             f"quiz answer status is invalid: {status}")
    _require(
        any(question["id"] == question_id for question in session["questions"]),
        f"quiz question not found: {question_id}",
    )
    answer_status = status
    answer_value = value.strip() if isinstance(value, str) else ""
    if not answer_value:
        answer_status = "unknown" if status == "unknown" else "skipped"
        answer_value = answer_status
    answered_at = _timestamp(now)
    session["answers"].append({
        "question_id": question_id,
        "value": answer_value,
        "status": answer_status,
        "source": {
            "ref": source_ref,
            "observed_at": answered_at,
        },
        "answered_at": answered_at,
    })
    latest = {
        answer["question_id"] for answer in session["answers"]
    }
    if all(question["id"] in latest for question in session["questions"]):
        session["status"] = "complete"
    session["updated_at"] = answered_at
    quiz["updated_at"] = answered_at
    validate_quiz(quiz)
    _atomic_write_json(_dependency("quiz_path")(repo), quiz)
    return _quiz_status(session)


def quiz_status(repo: Path, session_id: str) -> dict[str, Any]:
    quiz = load_quiz(repo)
    session = next(
        (item for item in quiz["sessions"] if item["id"] == session_id),
        None,
    )
    _require(session is not None, f"quiz session not found: {session_id}")
    return _quiz_status(session)


def _target_fingerprint(data: dict[str, Any], target: str) -> str:
    payload = {
        "definition": data["targets"][target]["definition"],
        "pillars": _dependency("score_inputs")(data, target),
    }
    for outcomes in payload["pillars"].values():
        for outcome_id in list(outcomes):
            outcomes[outcome_id] = None
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:16]


def _delivery_score(
    previous_inputs: dict[str, dict[str, int]],
    current_inputs: dict[str, dict[str, int]],
) -> int | None:
    held_structure: dict[str, dict[str, int]] = {}
    for pillar_id, previous_outcomes in previous_inputs.items():
        held_structure[pillar_id] = {}
        current_outcomes = current_inputs.get(pillar_id, {})
        for outcome_id, previous_maturity in previous_outcomes.items():
            held_structure[pillar_id][outcome_id] = current_outcomes.get(
                outcome_id, previous_maturity
            )
    return _dependency("score_from_inputs")(held_structure)
