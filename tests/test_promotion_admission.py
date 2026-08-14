from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import cast

from scripts import promotion_admission, promotion_admission_contracts
from tests.fixtures.promotion_admission import (
    PromotionAdmissionMixin,
    _approval,
    _candidate,
    _editorial_projection,
    _external_candidate,
    _external_projection,
    _private_candidate,
    _private_projection,
    _projection,
)


class PromotionAdmissionContractTests(PromotionAdmissionMixin, unittest.TestCase):
    def test_public_facade_preserves_contract_exports(self) -> None:
        for name in (
            "AdmissionError",
            "build_plan",
            "candidate_preflight_findings",
            "load_json",
            "validate_approval",
            "validate_candidate",
            "validate_projection",
        ):
            self.assertIs(
                getattr(promotion_admission, name),
                getattr(promotion_admission_contracts, name),
            )

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
