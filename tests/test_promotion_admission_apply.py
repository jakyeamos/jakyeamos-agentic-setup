from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import cast

from scripts.catalog_validation import load_manifest
from tests.fixtures.promotion_admission import (
    PromotionAdmissionMixin,
    ROOT,
    _approval,
    _candidate,
    _editorial_projection,
    _external_candidate,
    _external_projection,
    _private_candidate,
    _private_projection,
    _projection,
)


class PromotionAdmissionApplyTests(PromotionAdmissionMixin, unittest.TestCase):
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
