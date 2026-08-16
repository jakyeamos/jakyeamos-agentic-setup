from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import cast

from scripts.catalog_validation import load_manifest
from scripts.promotion_admission import main

ROOT = Path(__file__).resolve().parents[1]


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


class PromotionAdmissionTests(unittest.TestCase):
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

    def test_validation_keeps_private_candidate_evidence_out_of_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            candidate_path.write_text(json.dumps(_candidate()), encoding="utf-8")
            projection_path.write_text(
                json.dumps(_projection("candidate-admission-fixture")), encoding="utf-8"
            )

            result, payload, output = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(payload["status"], "review_required")
            self.assertFalse(payload["mutated"])
            self.assertNotIn("private-source-marker", output)
            self.assertNotIn("private-evidence-marker", output)

    def test_validation_reports_status_and_private_path_boundaries_together(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = _candidate()
            candidate["status"] = "promoted"
            candidate["title"] = "/private/team/secrets.txt"
            candidate_path = root / "candidate.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")

            result, payload, output = self._run(
                ["validate", "--candidate", str(candidate_path)]
            )

            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            errors = cast(list[str], payload["validation_errors"])
            self.assertIn(
                "candidate contains a private absolute path or credential-shaped value",
                errors,
            )
            self.assertIn(
                "candidate must remain in candidate status for JAS admission", errors
            )
            self.assertEqual(payload["candidate_state"], "promoted")
            self.assertFalse(payload["mutated"])
            self.assertNotIn("/private/team/secrets.txt", output)

    def test_v3_projection_carries_complete_editorial_metadata_into_the_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            candidate_path.write_text(json.dumps(_candidate()), encoding="utf-8")
            projection_path.write_text(
                json.dumps(_editorial_projection("candidate-admission-fixture")),
                encoding="utf-8",
            )

            result, payload, _ = self._run(
                [
                    "plan",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(payload["schema_version"], "jas-promotion-projection/v3")
            asset = cast(dict[str, object], payload["asset"])
            editorial = cast(dict[str, object], asset["editorial"])
            self.assertEqual(editorial["type"], "setup")
            self.assertEqual(editorial["use_cases"], ["prepare-agent-host"])

    def test_v3_projection_rejects_incomplete_editorial_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            projection = _editorial_projection("candidate-admission-fixture")
            asset = cast(dict[str, object], projection["asset"])
            editorial = cast(dict[str, object], asset["editorial"])
            editorial["use_cases"] = []
            candidate_path.write_text(json.dumps(_candidate()), encoding="utf-8")
            projection_path.write_text(json.dumps(projection), encoding="utf-8")

            result, payload, _ = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )

            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn("non-empty list", str(payload["error"]))

    def test_v3_projection_cannot_enter_the_private_overlay_lane(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            projection = _editorial_projection("candidate-admission-fixture")
            projection["visibility"] = "private-overlay"
            candidate_path.write_text(json.dumps(_candidate()), encoding="utf-8")
            projection_path.write_text(json.dumps(projection), encoding="utf-8")

            result, payload, _ = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )

            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn("requires public visibility", str(payload["error"]))

    def test_admit_requires_explicit_approval_and_emits_manifest_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            approval_path = root / "approval.json"
            candidate_path.write_text(json.dumps(_candidate()), encoding="utf-8")
            projection_path.write_text(
                json.dumps(_projection("candidate-admission-fixture")), encoding="utf-8"
            )
            approval_path.write_text(
                json.dumps(_approval("candidate-admission-fixture")), encoding="utf-8"
            )

            result, pending, _ = self._run(
                [
                    "plan",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )
            self.assertEqual(result, 0)
            self.assertEqual(pending["status"], "review_required")

            result, admitted, output = self._run(
                [
                    "admit",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                    "--approval",
                    str(approval_path),
                ]
            )
            self.assertEqual(result, 0)
            self.assertEqual(admitted["status"], "ready_for_manifest_review")
            self.assertEqual(admitted["target"], "catalog/manifest.json")
            self.assertFalse(admitted["mutated"])
            self.assertNotIn("private-source-marker", output)
            self.assertNotIn("private-evidence-marker", output)

    def test_reference_only_candidate_emits_external_manifest_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = _external_candidate()
            candidate_id = str(candidate["candidate_id"])
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            approval_path = root / "approval.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            projection_path.write_text(
                json.dumps(_external_projection(candidate_id)), encoding="utf-8"
            )
            approval_path.write_text(json.dumps(_approval(candidate_id)), encoding="utf-8")

            result, pending, _ = self._run(
                [
                    "plan",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )
            self.assertEqual(result, 0)
            self.assertEqual(pending["status"], "review_required")
            self.assertEqual(pending["target"], "catalog/manifest.json")
            self.assertEqual(
                cast(dict[str, object], pending["source_map_entry"])["class"],
                "external",
            )

            result, admitted, _ = self._run(
                [
                    "admit",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                    "--approval",
                    str(approval_path),
                ]
            )
            self.assertEqual(result, 0)
            self.assertEqual(admitted["status"], "ready_for_manifest_review")
            self.assertFalse(admitted["mutated"])
            self.assertEqual(
                cast(dict[str, object], admitted["asset"])["asset_class"],
                "external",
            )

    def test_external_projection_requires_reference_only_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = _candidate()
            candidate_id = str(candidate["candidate_id"])
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            projection_path.write_text(
                json.dumps(_external_projection(candidate_id)), encoding="utf-8"
            )

            result, payload, _ = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )
            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn(
                "external public projection requires a reference-only candidate",
                str(payload["error"]),
            )

    def test_reference_only_candidate_requires_external_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = _external_candidate()
            candidate_id = str(candidate["candidate_id"])
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            projection_path.write_text(
                json.dumps(_projection(candidate_id)), encoding="utf-8"
            )

            result, payload, _ = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )
            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn(
                "reference-only candidate requires an external public projection",
                str(payload["error"]),
            )

    def test_external_projection_requires_a_public_url(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = _external_candidate()
            candidate_id = str(candidate["candidate_id"])
            projection = _external_projection(candidate_id)
            asset = cast(dict[str, object], projection["asset"])
            asset["external_links"] = []
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            projection_path.write_text(json.dumps(projection), encoding="utf-8")

            result, payload, _ = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )
            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn(
                "external public projection requires at least one public URL",
                str(payload["error"]),
            )

    def test_private_overlay_requires_a_catalog_asset_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            candidate_path.write_text(json.dumps(_candidate()), encoding="utf-8")
            projection_path.write_text(
                json.dumps(
                    _projection(
                        "candidate-admission-fixture", visibility="private-overlay"
                    )
                ),
                encoding="utf-8",
            )

            result, payload, _ = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )

            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(
                payload["reason"], "private_overlay_requires_catalog_asset_reference"
            )

    def test_private_projection_emits_a_reviewable_installable_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            approval_path = root / "approval.json"
            candidate = _private_candidate()
            candidate_id = str(candidate["candidate_id"])
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            projection_path.write_text(
                json.dumps(_private_projection(candidate_id)), encoding="utf-8"
            )
            approval_path.write_text(json.dumps(_approval(candidate_id)), encoding="utf-8")

            result, pending, output = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )
            self.assertEqual(result, 0)
            self.assertEqual(pending["status"], "review_required")
            self.assertEqual(pending["schema_version"], "jas-promotion-projection/v2")
            self.assertEqual(pending["target"], "private-overlay.json")
            self.assertNotIn("private-source-marker", output)
            self.assertNotIn("private-evidence-marker", output)

            result, admitted, output = self._run(
                [
                    "admit",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                    "--approval",
                    str(approval_path),
                ]
            )
            self.assertEqual(result, 0)
            self.assertEqual(admitted["status"], "ready_for_overlay_review")
            self.assertEqual(admitted["target"], "private-overlay.json")
            self.assertFalse(admitted["mutated"])
            overlay = cast(dict[str, object], admitted["overlay"])
            self.assertEqual(overlay["schema_version"], "jas-private-overlay/v2")
            self.assertEqual(overlay["visibility"], "private-overlay")
            self.assertEqual(len(cast(list[object], overlay["private_assets"])), 1)
            self.assertNotIn("private-source-marker", output)
            self.assertNotIn("private-evidence-marker", output)

    def test_private_projection_must_match_the_candidate_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            candidate = _private_candidate()
            candidate_id = str(candidate["candidate_id"])
            projection = _private_projection(candidate_id)
            asset = cast(dict[str, object], projection["private_asset"])
            asset["package_ref"] = "artifact:private-package:other"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            projection_path.write_text(json.dumps(projection), encoding="utf-8")

            result, payload, output = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )
            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertNotIn("private-source-marker", output)

    def test_private_candidate_requires_a_package_before_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            candidate = _private_candidate()
            candidate.pop("private_package")
            candidate_id = str(candidate["candidate_id"])
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            projection_path.write_text(
                json.dumps(_private_projection(candidate_id)), encoding="utf-8"
            )

            result, payload, output = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )
            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertIn("private candidate requires private_package", output)

    def test_apply_requires_the_explicit_apply_flag_and_keeps_public_catalog_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_repo_for_catalog_apply(temporary)
            candidate = _candidate()
            candidate_id = str(candidate["candidate_id"])
            candidate["promotion_projection"] = _projection(candidate_id)
            candidate_path = Path(temporary) / "candidate.json"
            approval_path = Path(temporary) / "approval.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            approval_path.write_text(json.dumps(_approval(candidate_id)), encoding="utf-8")
            manifest_path = root / "catalog" / "manifest.json"
            before = manifest_path.read_bytes()

            result, payload, _ = self._run_at(
                root,
                [
                    "apply",
                    "--candidate",
                    str(candidate_path),
                    "--approval",
                    str(approval_path),
                    "--mode",
                    "public",
                ],
            )

            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["reason"], "apply_requires_explicit_flag")
            self.assertFalse(payload["mutated"])
            self.assertEqual(manifest_path.read_bytes(), before)

    def test_public_apply_updates_a_copy_of_the_catalog_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_repo_for_catalog_apply(temporary)
            candidate = _candidate()
            candidate_id = str(candidate["candidate_id"])
            candidate["promotion_projection"] = _editorial_projection(candidate_id)
            candidate_path = Path(temporary) / "candidate.json"
            approval_path = Path(temporary) / "approval.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            approval_path.write_text(json.dumps(_approval(candidate_id)), encoding="utf-8")
            arguments = [
                "apply",
                "--candidate",
                str(candidate_path),
                "--approval",
                str(approval_path),
                "--mode",
                "public",
                "--apply",
            ]

            result, applied, output = self._run_at(root, arguments)

            self.assertEqual(result, 0)
            self.assertEqual(applied["status"], "JAS_APPLIED")
            self.assertTrue(applied["mutated"])
            manifest = load_manifest(root)
            assets = cast(list[dict[str, object]], manifest["assets"])
            self.assertEqual(
                sum(1 for asset in assets if asset["id"] == candidate_id), 1
            )
            admitted = next(asset for asset in assets if asset["id"] == candidate_id)
            editorial = cast(dict[str, object], admitted["editorial"])
            self.assertEqual(editorial["type"], "setup")
            self.assertEqual(editorial["use_cases"], ["prepare-agent-host"])
            source_map = cast(list[dict[str, object]], manifest["source_map"])
            self.assertEqual(
                sum(
                    1
                    for source in source_map
                    if source["source_id"] == "leverage-promotion-candidate"
                ),
                1,
            )
            after_first_apply = (root / "catalog" / "manifest.json").read_bytes()
            self.assertNotIn("private-source-marker", output)
            self.assertNotIn("private-evidence-marker", output)

            result, already_applied, _ = self._run_at(root, arguments)

            self.assertEqual(result, 0)
            self.assertEqual(already_applied["status"], "JAS_ALREADY_APPLIED")
            self.assertFalse(already_applied["mutated"])
            self.assertEqual(
                (root / "catalog" / "manifest.json").read_bytes(), after_first_apply
            )

    def test_reference_only_public_apply_updates_catalog_without_installing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_repo_for_catalog_apply(temporary)
            candidate = _external_candidate()
            candidate_id = str(candidate["candidate_id"])
            candidate["promotion_projection"] = _external_projection(candidate_id)
            candidate_path = Path(temporary) / "candidate.json"
            approval_path = Path(temporary) / "approval.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            approval_path.write_text(json.dumps(_approval(candidate_id)), encoding="utf-8")

            result, applied, _ = self._run_at(
                root,
                [
                    "apply",
                    "--candidate",
                    str(candidate_path),
                    "--approval",
                    str(approval_path),
                    "--mode",
                    "public",
                    "--apply",
                ],
            )

            self.assertEqual(result, 0)
            self.assertEqual(applied["status"], "JAS_APPLIED")
            self.assertTrue(applied["mutated"])
            manifest = load_manifest(root)
            assets = cast(list[dict[str, object]], manifest["assets"])
            admitted = next(asset for asset in assets if asset["id"] == candidate_id)
            self.assertEqual(admitted["asset_class"], "external")
            self.assertEqual(
                admitted["external_links"],
                ["https://github.com/jakyeamos/mac-control"],
            )
            self.assertEqual(admitted["files"], [])
            self.assertFalse((root / "workbench" / candidate_id).exists())

    def test_private_apply_installs_the_private_package_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = ROOT
            candidate = _private_candidate()
            candidate_id = str(candidate["candidate_id"])
            candidate["promotion_projection"] = _private_projection(candidate_id)
            candidate_path = Path(temporary) / "candidate.json"
            approval_path = Path(temporary) / "approval.json"
            overlay_path = Path(temporary) / "config" / "private-overlay.json"
            private_root = Path(temporary) / "private-packages"
            package_root = private_root / "candidate-admission-private"
            target_root = Path(temporary) / "target"
            package_root.mkdir(parents=True)
            (package_root / "SKILL.md").write_text("private skill\n", encoding="utf-8")
            (package_root / "WORKFLOW.md").write_text(
                "private workflow\n", encoding="utf-8"
            )
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            approval_path.write_text(json.dumps(_approval(candidate_id)), encoding="utf-8")
            arguments = [
                "apply",
                "--candidate",
                str(candidate_path),
                "--approval",
                str(approval_path),
                "--mode",
                "private",
                "--overlay-path",
                str(overlay_path),
                "--private-root",
                str(private_root),
                "--target-root",
                str(target_root),
                "--apply",
            ]

            result, applied, _ = self._run_at(root, arguments)

            self.assertEqual(result, 0)
            self.assertEqual(applied["status"], "JAS_APPLIED")
            self.assertTrue(applied["mutated"])
            self.assertTrue(overlay_path.is_file())
            self.assertEqual(
                (target_root / ".codex" / "workbench" / candidate_id / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
                "private skill\n",
            )
            self.assertEqual(
                (target_root / ".codex" / "workbench" / candidate_id / "WORKFLOW.md").read_text(
                    encoding="utf-8"
                ),
                "private workflow\n",
            )
            overlay_after_first_apply = overlay_path.read_bytes()

            result, already_applied, _ = self._run_at(root, arguments)

            self.assertEqual(result, 0)
            self.assertEqual(already_applied["status"], "JAS_ALREADY_APPLIED")
            self.assertFalse(already_applied["mutated"])
            self.assertEqual(overlay_path.read_bytes(), overlay_after_first_apply)

    def test_both_apply_commits_public_catalog_and_personal_overlay_together(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_repo_for_catalog_apply(temporary)
            candidate = _candidate()
            candidate_id = str(candidate["candidate_id"])
            candidate["promotion_projection"] = _projection(candidate_id)
            candidate_path = Path(temporary) / "candidate.json"
            approval_path = Path(temporary) / "approval.json"
            overlay_path = Path(temporary) / "config" / "private-overlay.json"
            target_root = Path(temporary) / "target"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            approval_path.write_text(json.dumps(_approval(candidate_id)), encoding="utf-8")

            result, applied, _ = self._run_at(
                root,
                [
                    "apply",
                    "--candidate",
                    str(candidate_path),
                    "--approval",
                    str(approval_path),
                    "--mode",
                    "both",
                    "--overlay-path",
                    str(overlay_path),
                    "--target-root",
                    str(target_root),
                    "--apply",
                ],
            )

            self.assertEqual(result, 0)
            self.assertEqual(applied["status"], "JAS_APPLIED")
            self.assertTrue(applied["mutated"])
            manifest = load_manifest(root)
            self.assertIn(
                candidate_id,
                [str(asset["id"]) for asset in cast(list[dict[str, object]], manifest["assets"])],
            )
            self.assertTrue(overlay_path.is_file())
            self.assertTrue(
                (target_root / "workbench" / "adapters" / "generic" / "WORKBENCH.md").is_file()
            )

    def test_private_projection_value_is_rejected_without_echoing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            projection = _projection("candidate-admission-fixture")
            asset = cast(dict[str, object], projection["asset"])
            private_marker = "/" + "Users" + "/example/private-not-for-public-use"
            asset["summary"] = private_marker
            candidate_path.write_text(json.dumps(_candidate()), encoding="utf-8")
            projection_path.write_text(json.dumps(projection), encoding="utf-8")

            result, payload, output = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )

            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertNotIn(private_marker, output)

    def test_private_candidate_identifier_is_rejected_without_echoing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_path = root / "candidate.json"
            projection_path = root / "projection.json"
            private_marker = "/" + "Users" + "/private-candidate"
            candidate = _candidate()
            candidate["candidate_id"] = private_marker
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            projection_path.write_text(
                json.dumps(_projection(private_marker)), encoding="utf-8"
            )

            result, payload, output = self._run(
                [
                    "validate",
                    "--candidate",
                    str(candidate_path),
                    "--projection",
                    str(projection_path),
                ]
            )

            self.assertEqual(result, 2)
            self.assertEqual(payload["status"], "blocked")
            self.assertNotIn(private_marker, output)


if __name__ == "__main__":
    unittest.main()
