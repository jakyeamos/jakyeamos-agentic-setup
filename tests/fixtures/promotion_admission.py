"""Fixture builders only; assertions live in the two test_promotion_admission modules."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import tempfile
from pathlib import Path
from typing import cast

from scripts.catalog_validation import load_manifest
from scripts.promotion_admission import main

ROOT = Path(__file__).resolve().parents[2]


def _candidate() -> dict[str, object]:
    return {
        "schema_version": "leverage-promotion-candidate/v1",
        "visibility": "private",
        "candidate_id": "candidate-admission-fixture",
        "created_at": "2026-08-04T12:00:00+00:00",
        "title": "Private source candidate",
        "asset_kind": "workflow",
        "source_refs": ["private-source-marker"],
        "portable_artifact_refs": ["artifact:sanitized:fixture"],
        "trigger": "A recurring bounded failure is observed.",
        "non_trigger": "No recurring failure is observed.",
        "expected_behavior": "The workflow produces a reviewable result.",
        "input_contract": ["task context"],
        "output_contract": ["reviewable result"],
        "decision_path": ["observe", "test", "review"],
        "safety_boundary": ["private evidence stays local"],
        "verifier": ["clean-room positive and negative fixtures"],
        "stopping_condition": "Stop when the verifier passes or a blocker is recorded.",
        "clean_room_fixture_ref": "fixture:admission",
        "evidence_refs": ["private-evidence-marker"],
        "quantification": {"metric": "manual minutes", "baseline": 30, "observed": 10},
        "portability": "portable",
        "redaction_notes": ["private source details remain in the candidate"],
        "status": "candidate",
        "review_status": "pending",
        "maturity": "experimental",
    }


def _projection(candidate_id: str, *, visibility: str = "public") -> dict[str, object]:
    manifest = load_manifest(ROOT)
    assets = cast(list[dict[str, object]], manifest["assets"])
    asset = copy.deepcopy(
        next(item for item in assets if item["id"] == "adapter-generic")
    )
    asset["id"] = "candidate-admission-fixture"
    asset["title"] = "Sanitized candidate fixture"
    asset["summary"] = "A sanitized fixture projection for admission testing."
    asset["provenance"] = {
        "status": "sanitized-derived",
        "source": "leverage-promotion-candidate",
        "license_status": "MIT-compatible",
        "redistribution": "allowed",
    }
    asset["evidence"] = ["docs/mining.md"]
    return {
        "schema_version": "jas-promotion-projection/v1",
        "visibility": visibility,
        "candidate_id": candidate_id,
        "asset": asset,
    }


def _editorial_projection(candidate_id: str) -> dict[str, object]:
    projection = _projection(candidate_id)
    projection["schema_version"] = "jas-promotion-projection/v3"
    asset = cast(dict[str, object], projection["asset"])
    asset["editorial"] = {
        "type": "setup",
        "topics": ["agent-configuration", "host-adapters"],
        "use_cases": ["prepare-agent-host"],
        "why": "Prepare a portable workbench for one supported agent host.",
        "use_when": "Use when a host needs explicit, reviewable setup metadata.",
        "avoid_when": "Avoid when the host is unsupported or no installation is needed.",
    }
    return projection


def _external_candidate() -> dict[str, object]:
    candidate = _candidate()
    candidate["candidate_id"] = "candidate-external-reference"
    candidate["title"] = "Public project reference"
    candidate["asset_kind"] = "reference"
    candidate.pop("portable_artifact_refs")
    candidate["portability"] = "reference-only"
    return candidate


def _external_projection(candidate_id: str) -> dict[str, object]:
    manifest = load_manifest(ROOT)
    assets = cast(list[dict[str, object]], manifest["assets"])
    asset = copy.deepcopy(
        next(item for item in assets if item["id"] == "reference-aios")
    )
    asset["id"] = candidate_id
    asset["title"] = "Public project reference"
    asset["summary"] = "A separately owned public project reference."
    asset["provenance"] = {
        "status": "sanitized-derived",
        "source": "leverage-promotion-candidate",
        "license_status": "reference-only",
        "redistribution": "reference-only",
    }
    asset["external_links"] = ["https://github.com/jakyeamos/mac-control"]
    asset["evidence"] = ["docs/external-references.md"]
    return {
        "schema_version": "jas-promotion-projection/v1",
        "visibility": "public",
        "candidate_id": candidate_id,
        "asset": asset,
    }


def _private_candidate() -> dict[str, object]:
    candidate = _candidate()
    candidate["candidate_id"] = "candidate-admission-private"
    candidate.pop("portable_artifact_refs")
    candidate["portability"] = "private"
    candidate["disposition_reason"] = "Personal workflow port; not for public distribution."
    candidate["private_package"] = {
        "schema_version": "leverage-private-package/v1",
        "package_id": "candidate-admission-private",
        "package_ref": "artifact:private-package:candidate-admission-private",
        "files": ["SKILL.md", "WORKFLOW.md"],
        "entrypoints": ["SKILL.md"],
        "redaction_status": "sanitized",
        "redaction_notes": ["private source details removed before packaging"],
    }
    return candidate


def _private_projection(candidate_id: str) -> dict[str, object]:
    return {
        "schema_version": "jas-promotion-projection/v2",
        "visibility": "private-overlay",
        "candidate_id": candidate_id,
        "private_asset": {
            "id": candidate_id.replace("_", "-"),
            "kind": "workflow",
            "title": "Sanitized private workflow",
            "summary": "A private workflow port with a reviewable installation contract.",
            "maturity": "experimental",
            "supported_targets": ["codex"],
            "package_ref": "artifact:private-package:candidate-admission-private",
            "package_dir": "candidate-admission-private",
            "entrypoints": ["SKILL.md"],
            "files": ["SKILL.md", "WORKFLOW.md"],
            "install": {
                "mode": "copy",
                "destination": "$HOME/.codex/workbench/candidate-admission-private",
            },
        },
    }


def _approval(candidate_id: str) -> dict[str, object]:
    return {
        "schema_version": "jas-promotion-approval/v1",
        "candidate_id": candidate_id,
        "decision": "approve",
        "reviewer": "human-review",
        "reviewed_at": "2026-08-04T12:30:00+00:00",
    }


class PromotionAdmissionMixin:
    def _run(self, arguments: list[str]) -> tuple[int, dict[str, object], str]:
        return self._run_at(ROOT, arguments)

    def _run_at(
        self, root: Path, arguments: list[str]
    ) -> tuple[int, dict[str, object], str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([*arguments, "--root", str(root), "--json"])
        payload = cast(dict[str, object], json.loads(output.getvalue()))
        return result, payload, output.getvalue()

    def _copy_repo_for_catalog_apply(self, temporary: str) -> Path:
        destination = Path(temporary) / "jas-copy"
        shutil.copytree(
            ROOT,
            destination,
            ignore=shutil.ignore_patterns(
                ".git",
                ".mac-control",
                ".project-compass",
                "node_modules",
                ".venv",
                "target",
            ),
        )
        return destination
