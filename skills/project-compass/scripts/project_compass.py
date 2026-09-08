#!/usr/bin/env python3
"""Validate, score, and checkpoint a Project Compass contract."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import compass_extensions as _compass_extensions

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
ID_PATTERN = _compass_extensions.ID_PATTERN
COMPASS_KINDS = _compass_extensions.COMPASS_KINDS
COMPASS_STATUSES = _compass_extensions.COMPASS_STATUSES
LINK_KINDS = _compass_extensions.LINK_KINDS
LINK_STATUSES = _compass_extensions.LINK_STATUSES
QUIZ_MODES = _compass_extensions.QUIZ_MODES
QUIZ_STATUSES = _compass_extensions.QUIZ_STATUSES
QUIZ_ANSWER_STATUSES = _compass_extensions.QUIZ_ANSWER_STATUSES


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




_compass_extensions.configure(
    contract_error=ContractError,
    id_pattern=ID_PATTERN,
    require=_require,
    validate_timestamp=_validate_timestamp,
    validate_source=_validate_source,
    validate_relative_path=_validate_relative_path,
    load_contract=load_contract,
    validate_contract=validate_contract,
    contract_path=_contract_path,
    registry_path=_registry_path,
    quiz_path=_quiz_path,
    score_contract=score_contract,
    score_inputs=_score_inputs,
    score_from_inputs=_score_from_inputs,
)
validate_registry = _compass_extensions.validate_registry
load_registry = _compass_extensions.load_registry
load_compass_family = _compass_extensions.load_compass_family
validate_quiz = _compass_extensions.validate_quiz
load_quiz = _compass_extensions.load_quiz
score_compass_family = _compass_extensions.score_compass_family
start_quiz = _compass_extensions.start_quiz
answer_quiz = _compass_extensions.answer_quiz
quiz_status = _compass_extensions.quiz_status
_target_fingerprint = _compass_extensions._target_fingerprint
_delivery_score = _compass_extensions._delivery_score


def main(argv: list[str] | None = None) -> int:
    from compass_cli import main as cli_main
    return cli_main(argv)


if __name__ == "__main__":
    # Ensure the CLI and extensions share this entrypoint module instance.
    sys.modules["project_compass"] = sys.modules[__name__]
    raise SystemExit(main())
