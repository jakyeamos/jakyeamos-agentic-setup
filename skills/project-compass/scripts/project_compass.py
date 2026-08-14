#!/usr/bin/env python3
"""Validate, score, and checkpoint a Project Compass contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MATURITY_VALUES = {0, 25, 50, 75, 100}
CONFIDENCE_VALUES = {"low": 0.25, "medium": 0.6, "high": 1.0}
TARGETS = ("mvp", "complete_product")
LAYERS = ("intended", "planned", "implemented", "verified")
BLOCKER_KINDS = {
    "product-decision",
    "technical",
    "external",
    "sequencing",
    "verification",
}
DRIFT_KINDS = {
    "intent-change",
    "planning-drift",
    "implementation-drift",
    "verification-gap",
    "stale-source",
    "conflict",
}
DRIFT_STATUSES = {"open", "accepted", "resolved", "superseded"}
CONTINUITY_COMMITMENT_KINDS = {
    "goal", "constraint", "decision", "rationale", "open-question",
}
CONTINUITY_COMMITMENT_STATUSES = {"active", "unresolved", "superseded", "retired"}
CONTINUITY_CLASSIFICATIONS = {
    "additive", "clarifying", "corrective", "conflicting", "superseding",
}
CONTINUITY_MATERIALITIES = {"low", "medium", "high"}
CONTINUITY_DISPOSITIONS = {
    "proceed", "proceed-with-preservation", "pending-question",
    "recorded-supersession",
}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COMPASS_KINDS = {"root", "subsystem"}
COMPASS_STATUSES = {"active", "draft", "retired"}
LINK_KINDS = {"depends-on", "handoff", "shared-invariant"}
LINK_STATUSES = {"aligned", "unknown", "blocked", "drift"}
QUIZ_MODES = {"greenfield", "brownfield", "realignment"}
QUIZ_STATUSES = {"active", "complete", "abandoned"}
QUIZ_ANSWER_STATUSES = {"explicit", "tentative", "unknown", "skipped"}


class ContractError(ValueError):
    """Raised when the Compass contract is invalid."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _validate_timestamp(value: Any, path: str) -> None:
    _require(isinstance(value, str) and value.strip(),
             f"{path} must be a non-empty timestamp")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{path} must be an ISO-8601 timestamp") from exc


def _validate_source(value: Any, path: str) -> None:
    _require(isinstance(value, dict), f"{path} must be an object")
    _require(isinstance(value.get("ref"), str) and value["ref"].strip(),
             f"{path}.ref must be a non-empty string")
    _validate_timestamp(value.get("observed_at"), f"{path}.observed_at")
    if "note" in value:
        _require(isinstance(value["note"], str), f"{path}.note must be a string")


def _validate_relative_path(value: Any, path: str) -> None:
    _require(isinstance(value, str) and value.strip(),
             f"{path} must be a non-empty relative path")
    candidate = Path(value)
    _require(not candidate.is_absolute() and not value.startswith("~"),
             f"{path} must be relative")
    _require(".." not in candidate.parts and "." not in candidate.parts,
             f"{path} must not contain traversal segments")


def _validate_scope(value: Any, path: str = "scope") -> None:
    _require(isinstance(value, dict), f"{path} must be an object")
    scope_id = value.get("id")
    _require(isinstance(scope_id, str) and ID_PATTERN.fullmatch(scope_id),
             f"{path}.id must be hyphen-case")
    kind = value.get("kind")
    _require(kind in COMPASS_KINDS, f"{path}.kind is invalid")
    parent_id = value.get("parent_id")
    if kind == "root":
        _require(parent_id is None, f"{path}.parent_id must be null for a root")
    else:
        _require(isinstance(parent_id, str)
                 and ID_PATTERN.fullmatch(parent_id),
                 f"{path}.parent_id must be a compass id for a subsystem")
        _require(parent_id != scope_id,
                 f"{path}.parent_id cannot reference itself")
    for field in ("purpose", "boundary"):
        _require(isinstance(value.get(field), str) and value[field].strip(),
                 f"{path}.{field} must be a non-empty string")
    for field in ("non_goals", "parent_outcomes", "paths"):
        _validate_string_array(value.get(field), f"{path}.{field}")
    for index, outcome_id in enumerate(value["parent_outcomes"]):
        _require(ID_PATTERN.fullmatch(outcome_id),
                 f"{path}.parent_outcomes[{index}] must be hyphen-case")
    for index, scope_path in enumerate(value["paths"]):
        _validate_relative_path(scope_path, f"{path}.paths[{index}]")


def _contract_path(repo: Path) -> Path:
    return repo / ".project-compass" / "contract.json"


def _continuity_path(repo: Path) -> Path:
    return repo / ".project-compass" / "continuity.json"


def _registry_path(repo: Path) -> Path:
    return repo / ".project-compass" / "compasses.json"


def _quiz_path(repo: Path) -> Path:
    return repo / ".project-compass" / "quiz.json"


def _history_path(repo: Path) -> Path:
    return repo / ".project-compass" / "checkpoints.jsonl"


def load_contract(repo: Path) -> dict[str, Any]:
    path = _contract_path(repo)
    _require(path.is_file(), f"contract not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read contract: {exc}") from exc
    _require(isinstance(data, dict), "contract root must be an object")
    return data


def validate_contract(data: dict[str, Any]) -> None:
    _require(data.get("schema_version") == 1, "schema_version must be 1")
    _require(isinstance(data.get("revision"), int) and data["revision"] >= 1,
             "revision must be an integer >= 1")

    project = data.get("project")
    _require(isinstance(project, dict), "project must be an object")
    for field in ("name", "identity", "audience", "core_loop", "north_star"):
        _require(isinstance(project.get(field), str) and project[field].strip(),
                 f"project.{field} must be a non-empty string")
    not_this = project.get("not_this")
    _require(isinstance(not_this, list) and all(
        isinstance(item, str) and item.strip() for item in not_this
    ), "project.not_this must be an array of non-empty strings")
    if "scope" in data:
        _validate_scope(data["scope"])

    targets = data.get("targets")
    _require(isinstance(targets, dict), "targets must be an object")
    for target in TARGETS:
        value = targets.get(target)
        _require(isinstance(value, dict), f"targets.{target} must be an object")
        _require(isinstance(value.get("definition"), str)
                 and value["definition"].strip(),
                 f"targets.{target}.definition must be a non-empty string")

    pillars = data.get("pillars")
    _require(isinstance(pillars, list) and pillars,
             "pillars must be a non-empty array")
    pillar_ids: set[str] = set()
    outcome_ids: set[str] = set()
    target_counts = {target: 0 for target in TARGETS}
    for pillar_index, pillar in enumerate(pillars):
        prefix = f"pillars[{pillar_index}]"
        _require(isinstance(pillar, dict), f"{prefix} must be an object")
        pillar_id = pillar.get("id")
        _require(isinstance(pillar_id, str) and ID_PATTERN.fullmatch(pillar_id),
                 f"{prefix}.id must be hyphen-case")
        _require(pillar_id not in pillar_ids, f"duplicate pillar id: {pillar_id}")
        pillar_ids.add(pillar_id)
        _require(isinstance(pillar.get("name"), str) and pillar["name"].strip(),
                 f"{prefix}.name must be a non-empty string")
        outcomes = pillar.get("outcomes")
        _require(isinstance(outcomes, list) and outcomes,
                 f"{prefix}.outcomes must be a non-empty array")
        for outcome_index, outcome in enumerate(outcomes):
            oprefix = f"{prefix}.outcomes[{outcome_index}]"
            _require(isinstance(outcome, dict), f"{oprefix} must be an object")
            outcome_id = outcome.get("id")
            _require(isinstance(outcome_id, str)
                     and ID_PATTERN.fullmatch(outcome_id),
                     f"{oprefix}.id must be hyphen-case")
            _require(outcome_id not in outcome_ids,
                     f"duplicate outcome id: {outcome_id}")
            outcome_ids.add(outcome_id)
            _require(isinstance(outcome.get("name"), str)
                     and outcome["name"].strip(),
                     f"{oprefix}.name must be a non-empty string")
            memberships = outcome.get("targets")
            _require(isinstance(memberships, list) and memberships,
                     f"{oprefix}.targets must be a non-empty array")
            _require(len(memberships) == len(set(memberships)),
                     f"{oprefix}.targets must be unique")
            _require(all(target in TARGETS for target in memberships),
                     f"{oprefix}.targets contains an unknown target")
            for target in memberships:
                target_counts[target] += 1
            _require(outcome.get("maturity") in MATURITY_VALUES,
                     f"{oprefix}.maturity must be one of {sorted(MATURITY_VALUES)}")
            _require(outcome.get("confidence") in CONFIDENCE_VALUES,
                     f"{oprefix}.confidence must be low, medium, or high")
            layers = outcome.get("layers")
            _require(isinstance(layers, dict), f"{oprefix}.layers must be an object")
            for layer in LAYERS:
                _require(isinstance(layers.get(layer), str)
                         and layers[layer].strip(),
                         f"{oprefix}.layers.{layer} must be a non-empty string")
            evidence = outcome.get("evidence")
            _require(isinstance(evidence, list),
                     f"{oprefix}.evidence must be an array")
            for evidence_index, source in enumerate(evidence):
                _validate_source(source, f"{oprefix}.evidence[{evidence_index}]")
            blockers = outcome.get("blockers")
            _require(isinstance(blockers, list),
                     f"{oprefix}.blockers must be an array")
            for blocker in blockers:
                _require(isinstance(blocker, dict)
                         and blocker.get("kind") in BLOCKER_KINDS
                         and isinstance(blocker.get("summary"), str)
                         and blocker["summary"].strip(),
                         f"{oprefix}.blockers contains an invalid blocker")

    for target, count in target_counts.items():
        _require(count > 0, f"target {target} has no outcomes")

    sources = data.get("source_layers")
    _require(isinstance(sources, dict), "source_layers must be an object")
    for layer in LAYERS:
        _require(isinstance(sources.get(layer), list),
                 f"source_layers.{layer} must be an array")
        for source_index, source in enumerate(sources[layer]):
            _validate_source(
                source, f"source_layers.{layer}[{source_index}]"
            )

    drift = data.get("drift")
    _require(isinstance(drift, list), "drift must be an array")
    for drift_index, item in enumerate(drift):
        prefix = f"drift[{drift_index}]"
        _require(isinstance(item, dict), f"{prefix} must be an object")
        _require(item.get("kind") in DRIFT_KINDS,
                 f"{prefix}.kind is invalid")
        _require(isinstance(item.get("summary"), str)
                 and item["summary"].strip(),
                 f"{prefix}.summary must be a non-empty string")
        _require(item.get("status") in DRIFT_STATUSES,
                 f"{prefix}.status is invalid")
        _validate_timestamp(item.get("observed_at"), f"{prefix}.observed_at")
        _require(isinstance(item.get("evidence"), list),
                 f"{prefix}.evidence must be an array")
        for source_index, source in enumerate(item["evidence"]):
            _validate_source(source, f"{prefix}.evidence[{source_index}]")
    _validate_timestamp(data.get("updated_at"), "updated_at")


def _validate_string_array(value: Any, path: str) -> None:
    _require(isinstance(value, list), f"{path} must be an array")
    _require(
        all(isinstance(item, str) and item.strip() for item in value),
        f"{path} must contain non-empty strings",
    )
    _require(len(value) == len(set(value)), f"{path} must contain unique strings")


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
        raise ContractError(f"cannot read {label}: {exc}") from exc
    _require(isinstance(data, dict), f"{label} root must be an object")
    return data


def load_registry(repo: Path) -> dict[str, Any]:
    data = _load_json_file(_registry_path(repo), "compass registry")
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
    root = load_contract(repo)
    validate_contract(root)
    registry_path = _registry_path(repo)
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
        validate_contract(contract)
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


def validate_continuity(data: dict[str, Any]) -> None:
    _require(isinstance(data, dict), "continuity root must be an object")
    _require(data.get("schema_version") == 1,
             "continuity.schema_version must be 1")
    _require(
        isinstance(data.get("revision"), int) and data["revision"] >= 1,
        "continuity.revision must be an integer >= 1",
    )
    commitments = data.get("commitments")
    _require(isinstance(commitments, list),
             "continuity.commitments must be an array")
    commitment_ids: set[str] = set()
    for index, commitment in enumerate(commitments):
        prefix = f"continuity.commitments[{index}]"
        _require(isinstance(commitment, dict), f"{prefix} must be an object")
        commitment_id = commitment.get("id")
        _require(
            isinstance(commitment_id, str) and ID_PATTERN.fullmatch(commitment_id),
            f"{prefix}.id must be hyphen-case",
        )
        _require(commitment_id not in commitment_ids,
                 f"duplicate continuity commitment id: {commitment_id}")
        commitment_ids.add(commitment_id)
        _require(commitment.get("kind") in CONTINUITY_COMMITMENT_KINDS,
                 f"{prefix}.kind is invalid")
        _require(
            isinstance(commitment.get("statement"), str)
            and commitment["statement"].strip(),
            f"{prefix}.statement must be a non-empty string",
        )
        _require(commitment.get("status") in CONTINUITY_COMMITMENT_STATUSES,
                 f"{prefix}.status is invalid")
        _validate_source(commitment.get("source"), f"{prefix}.source")

    reconciliations = data.get("reconciliations")
    _require(isinstance(reconciliations, list),
             "continuity.reconciliations must be an array")
    reconciliation_ids: set[str] = set()
    for index, reconciliation in enumerate(reconciliations):
        prefix = f"continuity.reconciliations[{index}]"
        _require(isinstance(reconciliation, dict), f"{prefix} must be an object")
        reconciliation_id = reconciliation.get("id")
        _require(
            isinstance(reconciliation_id, str)
            and ID_PATTERN.fullmatch(reconciliation_id),
            f"{prefix}.id must be hyphen-case",
        )
        _require(reconciliation_id not in reconciliation_ids,
                 f"duplicate continuity reconciliation id: {reconciliation_id}")
        reconciliation_ids.add(reconciliation_id)
        _validate_timestamp(reconciliation.get("observed_at"),
                            f"{prefix}.observed_at")
        _validate_source(reconciliation.get("source"), f"{prefix}.source")
        _require(reconciliation.get("classification") in CONTINUITY_CLASSIFICATIONS,
                 f"{prefix}.classification is invalid")
        _require(reconciliation.get("materiality") in CONTINUITY_MATERIALITIES,
                 f"{prefix}.materiality is invalid")
        _require(
            isinstance(reconciliation.get("incoming"), str)
            and reconciliation["incoming"].strip(),
            f"{prefix}.incoming must be a non-empty string",
        )
        project_evidence = reconciliation.get("project_evidence")
        _require(isinstance(project_evidence, list),
                 f"{prefix}.project_evidence must be an array")
        for source_index, source in enumerate(project_evidence):
            _validate_source(source, f"{prefix}.project_evidence[{source_index}]")
        for field in (
            "preserved", "changed", "contradicted", "deferred",
            "left_behind", "unknown",
        ):
            _validate_string_array(reconciliation.get(field), f"{prefix}.{field}")
        disposition = reconciliation.get("disposition")
        _require(disposition in CONTINUITY_DISPOSITIONS,
                 f"{prefix}.disposition is invalid")
        question = reconciliation.get("question")
        _require(isinstance(question, str), f"{prefix}.question must be a string")
        if disposition == "pending-question":
            _require(question.strip(), f"{prefix}.question is required while pending")
        if disposition == "recorded-supersession":
            _require(
                reconciliation.get("classification") == "superseding",
                f"{prefix}.recorded-supersession requires superseding classification",
            )
            _require(
                isinstance(reconciliation.get("reason"), str)
                and reconciliation["reason"].strip(),
                f"{prefix}.reason is required for recorded supersession",
            )
        if "reason" in reconciliation:
            _require(
                isinstance(reconciliation["reason"], str)
                and reconciliation["reason"].strip(),
                f"{prefix}.reason must be a non-empty string",
            )
        if "user_decision" in reconciliation:
            _require(
                isinstance(reconciliation["user_decision"], str)
                and reconciliation["user_decision"].strip(),
                f"{prefix}.user_decision must be a non-empty string",
            )
        if "decision_source" in reconciliation:
            _validate_source(reconciliation["decision_source"],
                             f"{prefix}.decision_source")
    _validate_timestamp(data.get("updated_at"), "continuity.updated_at")


def load_continuity(repo: Path) -> dict[str, Any]:
    path = _continuity_path(repo)
    _require(path.is_file(), f"continuity record not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read continuity record: {exc}") from exc
    validate_continuity(data)
    return data


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
    data = _load_json_file(_quiz_path(repo), "quiz sessions")
    validate_quiz(data)
    return data


def _validate_repo(repo: Path) -> dict[str, Any]:
    family = load_compass_family(repo)
    continuity_path = _continuity_path(repo)
    if continuity_path.exists():
        load_continuity(repo)
    quiz_path = _quiz_path(repo)
    if quiz_path.exists():
        load_quiz(repo)
    return family["contracts"][family["root_id"]]


def continuity_status(data: dict[str, Any]) -> dict[str, Any]:
    validate_continuity(data)
    active_statuses = {"active", "unresolved"}
    active_commitments = [
        commitment for commitment in data["commitments"]
        if commitment["status"] in active_statuses
    ]
    pending = [
        reconciliation for reconciliation in data["reconciliations"]
        if reconciliation["disposition"] == "pending-question"
    ]
    return {
        "revision": data["revision"],
        "active_commitments": active_commitments,
        "pending_reconciliations": pending,
        "counts": {
            "commitments": len(data["commitments"]),
            "active_commitments": len(active_commitments),
            "reconciliations": len(data["reconciliations"]),
            "pending_reconciliations": len(pending),
        },
        "updated_at": data["updated_at"],
    }


def _round_percent(value: float) -> int:
    return int(value + 0.5)


def _score_inputs(data: dict[str, Any], target: str) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for pillar in data["pillars"]:
        outcomes = {
            outcome["id"]: outcome["maturity"]
            for outcome in pillar["outcomes"]
            if target in outcome["targets"]
        }
        if outcomes:
            result[pillar["id"]] = outcomes
    return result


def _score_from_inputs(inputs: dict[str, dict[str, int]]) -> int | None:
    if not inputs:
        return None
    pillar_scores = [
        sum(outcomes.values()) / len(outcomes)
        for outcomes in inputs.values()
        if outcomes
    ]
    if not pillar_scores:
        return None
    return _round_percent(sum(pillar_scores) / len(pillar_scores))


def _confidence(data: dict[str, Any], target: str) -> tuple[str, int]:
    values = [
        CONFIDENCE_VALUES[outcome["confidence"]]
        for pillar in data["pillars"]
        for outcome in pillar["outcomes"]
        if target in outcome["targets"]
    ]
    if not values:
        return ("unknown", 0)
    percent = _round_percent(100 * sum(values) / len(values))
    label = "high" if percent >= 80 else "medium" if percent >= 50 else "low"
    return (label, percent)


def score_contract(data: dict[str, Any]) -> dict[str, Any]:
    validate_contract(data)
    result: dict[str, Any] = {}
    for target in TARGETS:
        inputs = _score_inputs(data, target)
        label, confidence_percent = _confidence(data, target)
        result[target] = {
            "progress_percent": _score_from_inputs(inputs),
            "confidence": label,
            "confidence_percent": confidence_percent,
            "pillars": {
                pillar: _score_from_inputs({pillar: outcomes})
                for pillar, outcomes in inputs.items()
            },
            "score_inputs": inputs,
        }
    return result


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
            "score": score_contract(family["contracts"][entry["id"]]),
        }
    return {
        "root_id": family["root_id"],
        "root": score_contract(family["contracts"][family["root_id"]]),
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


def _quiz_scope_kind(repo: Path, mode: str, compass_id: str) -> str:
    _require(mode in QUIZ_MODES, f"quiz mode is invalid: {mode}")
    contract_path = _contract_path(repo)
    if not contract_path.exists():
        _require(
            mode in {"greenfield", "brownfield"} and compass_id == "project",
            "a missing contract only supports a project greenfield or brownfield quiz",
        )
        return "root"
    family = load_compass_family(repo)
    _require(compass_id in family["contracts"],
             f"compass not found: {compass_id}")
    entry = next(item for item in family["entries"] if item["id"] == compass_id)
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
) -> dict[str, Any]:
    started_at = _timestamp(now)
    scope_kind = _quiz_scope_kind(repo, mode, compass_id)
    if session_id is None:
        suffix = datetime.fromisoformat(
            started_at.replace("Z", "+00:00")
        ).strftime("%Y%m%d%H%M%S%f")
        session_id = f"{mode}-{compass_id}-{suffix}"
    _require(ID_PATTERN.fullmatch(session_id) is not None,
             "quiz session_id must be hyphen-case")
    if _quiz_path(repo).exists():
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
        "scope_kind": scope_kind,
        "status": "active",
        "questions": _quiz_questions(mode, scope_kind),
        "answers": [],
        "started_at": started_at,
        "updated_at": started_at,
    }
    quiz["sessions"].append(session)
    quiz["updated_at"] = started_at
    validate_quiz(quiz)
    _atomic_write_json(_quiz_path(repo), quiz)
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
    _atomic_write_json(_quiz_path(repo), quiz)
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
        "pillars": _score_inputs(data, target),
    }
    for outcomes in payload["pillars"].values():
        for outcome_id in list(outcomes):
            outcomes[outcome_id] = None
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:16]


def _load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractError(
                f"invalid checkpoint JSON on line {line_number}: {exc}"
            ) from exc
        _require(isinstance(record, dict),
                 f"checkpoint line {line_number} must be an object")
        records.append(record)
    return records


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
    return _score_from_inputs(held_structure)


def _checkpoint_record(
    data: dict[str, Any],
    scores: dict[str, Any],
    previous: dict[str, Any] | None,
    note: str | None,
) -> dict[str, Any]:
    target_records: dict[str, Any] = {}
    for target in TARGETS:
        current = scores[target]
        progress = current["progress_percent"]
        delta = {"delivery": None, "scope": None, "total": None}
        if previous and target in previous.get("targets", {}):
            prior = previous["targets"][target]
            prior_progress = prior.get("progress_percent")
            prior_inputs = prior.get("score_inputs", {})
            held_score = _delivery_score(prior_inputs, current["score_inputs"])
            if isinstance(prior_progress, int) and isinstance(held_score, int):
                delivery = held_score - prior_progress
                total = progress - prior_progress
                delta = {
                    "delivery": delivery,
                    "scope": total - delivery,
                    "total": total,
                }
        target_records[target] = {
            "progress_percent": progress,
            "confidence": current["confidence"],
            "confidence_percent": current["confidence_percent"],
            "target_fingerprint": _target_fingerprint(data, target),
            "score_inputs": current["score_inputs"],
            "delta": delta,
        }

    blockers = [
        blocker
        for pillar in data["pillars"]
        for outcome in pillar["outcomes"]
        for blocker in outcome["blockers"]
    ]
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "contract_revision": data["revision"],
        "project": data["project"]["name"],
        "targets": target_records,
        "open_blockers": len(blockers),
        "open_drift": sum(
            1 for item in data["drift"] if item.get("status") == "open"
        ),
        "note": note or "",
    }


def _atomic_append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    content = existing + json.dumps(record, sort_keys=True) + "\n"
    fd, temporary_name = tempfile.mkstemp(
        prefix=".checkpoints.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def checkpoint(repo: Path, note: str | None) -> dict[str, Any]:
    data = _validate_repo(repo)
    scores = score_contract(data)
    history_path = _history_path(repo)
    history = _load_history(history_path)
    record = _checkpoint_record(data, scores, history[-1] if history else None, note)
    family = load_compass_family(repo)
    if family["registry"] is not None:
        family_scores = score_compass_family(repo)
        record["compass_family"] = {
            "root_id": family_scores["root_id"],
            "children": family_scores["children"],
            "alignment": family_scores["alignment"],
            "coverage": family_scores["coverage"],
        }
    _atomic_append_jsonl(history_path, record)
    return record


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "score"):
        child = subparsers.add_parser(command)
        child.add_argument("repo", type=Path)
        child.add_argument("--json", action="store_true")
    child = subparsers.add_parser("checkpoint")
    child.add_argument("repo", type=Path)
    child.add_argument("--note")
    child.add_argument("--json", action="store_true")
    child = subparsers.add_parser("continuity")
    child.add_argument("repo", type=Path)
    child.add_argument("--json", action="store_true")
    quiz = subparsers.add_parser("quiz")
    quiz_subparsers = quiz.add_subparsers(dest="quiz_command", required=True)
    start = quiz_subparsers.add_parser("start")
    start.add_argument("repo", type=Path)
    start.add_argument("--mode", choices=sorted(QUIZ_MODES), required=True)
    start.add_argument("--compass-id", default="project")
    start.add_argument("--session-id")
    start.add_argument("--now")
    start.add_argument("--json", action="store_true")
    answer = quiz_subparsers.add_parser("answer")
    answer.add_argument("repo", type=Path)
    answer.add_argument("--session-id", required=True)
    answer.add_argument("--question-id", required=True)
    answer.add_argument("--value", default="")
    answer.add_argument("--status", choices=sorted(QUIZ_ANSWER_STATUSES), default="explicit")
    answer.add_argument("--source-ref", default="conversation:user")
    answer.add_argument("--now")
    answer.add_argument("--json", action="store_true")
    status = quiz_subparsers.add_parser("status")
    status.add_argument("repo", type=Path)
    status.add_argument("--session-id", required=True)
    status.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        repo = args.repo.resolve()
        if args.command == "validate":
            _validate_repo(repo)
            result: dict[str, Any] = {"valid": True}
        elif args.command == "score":
            data = _validate_repo(repo)
            result = (
                score_compass_family(repo)
                if _registry_path(repo).exists()
                else score_contract(data)
            )
        elif args.command == "continuity":
            result = continuity_status(load_continuity(repo))
        elif args.command == "quiz":
            if args.quiz_command == "start":
                result = start_quiz(
                    repo,
                    args.mode,
                    compass_id=args.compass_id,
                    session_id=args.session_id,
                    now=args.now,
                )
            elif args.quiz_command == "answer":
                result = answer_quiz(
                    repo,
                    args.session_id,
                    args.question_id,
                    args.value,
                    status=args.status,
                    source_ref=args.source_ref,
                    now=args.now,
                )
            else:
                result = quiz_status(repo, args.session_id)
        else:
            result = checkpoint(repo, args.note)
    except ContractError as exc:
        if getattr(args, "json", False):
            print(json.dumps({"valid": False, "error": str(exc)}))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        print(json.dumps(result, indent=2, sort_keys=True))
    elif args.command == "validate":
        print("valid")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
