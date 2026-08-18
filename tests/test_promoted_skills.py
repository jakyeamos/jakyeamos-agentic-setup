from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.catalog_validation import load_manifest


REPO = Path(__file__).resolve().parents[1]
FORWARD_CASES = REPO / "fixtures/forward-tests.json"
VALIDATION_FAILURE_CASES = (
    REPO
    / "fixtures/consequence-closure/validation-failure-disposition.json"
)
COMPASS_OPERATIONS = ("add", "change", "remove", "fold")


class PromotedSkillTests(unittest.TestCase):
    def test_project_compass_is_the_only_authored_change_matrix(self) -> None:
        matrices = sorted(REPO.glob("skills/*/change-surface-matrix.json"))
        self.assertEqual(
            [path.relative_to(REPO).as_posix() for path in matrices],
            ["skills/project-compass/change-surface-matrix.json"],
        )
        matrix = json.loads(matrices[0].read_text(encoding="utf-8"))
        surface_ids = {surface["id"] for surface in matrix["surfaces"]}
        self.assertEqual(matrix["unresolved_surfaces"], [])
        self.assertIn("hosted-source", surface_ids)
        self.assertIn("installed-canonical-copy", surface_ids)
        self.assertIn("pronto-topology", surface_ids)
        self.assertIn("tmcp-contract-quality", surface_ids)
        self.assertIn("compass-family-truth", surface_ids)
        for surface in matrix["surfaces"]:
            self.assertEqual(tuple(surface["operations"]), COMPASS_OPERATIONS)
        closure = matrix["compass_closure"]
        self.assertEqual(closure["artifact_root"], ".project-compass/")
        self.assertEqual(tuple(closure["operations"]), COMPASS_OPERATIONS)
        for operation in COMPASS_OPERATIONS:
            fixture = json.loads(
                (
                    REPO
                    / f"fixtures/change-matrix/project-compass-{operation}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(fixture["operation"], operation)
            self.assertEqual(set(fixture["expected_surface_ids"]), surface_ids)
            self.assertTrue(fixture["assertions"])
            self.assertEqual(
                matrix["operation_evidence"][operation]["status"], "passed"
            )
            self.assertEqual(
                matrix["operation_evidence"][operation]["evidence"],
                [f"fixtures/change-matrix/project-compass-{operation}.json"],
            )

    def test_repository_matrix_routes_compass_family_lifecycle(self) -> None:
        matrix = json.loads(
            (REPO / ".agents/change-surface-matrix.json").read_text(encoding="utf-8")
        )
        surface = next(
            item for item in matrix["surfaces"] if item["id"] == "project-compass-family"
        )
        self.assertEqual(tuple(surface["operations"]), COMPASS_OPERATIONS)
        self.assertEqual(matrix["compass_closure"]["artifact_root"], ".project-compass/")
        self.assertEqual(
            tuple(matrix["compass_closure"]["operations"]), COMPASS_OPERATIONS
        )

    def test_each_promoted_skill_has_trigger_and_non_trigger_forward_cases(self) -> None:
        payload = json.loads(FORWARD_CASES.read_text(encoding="utf-8"))
        cases = payload["cases"]
        self.assertEqual(len(cases), 14)
        skills = {case["skill"] for case in cases}
        self.assertEqual(len(skills), len(cases))
        for case in cases:
            self.assertTrue(case["trigger"])
            self.assertTrue(case["non_trigger"])
            self.assertEqual(case["expected_trigger"], "invoke-skill")
            self.assertEqual(case["expected_non_trigger"], "do-not-invoke")

    def test_promoted_skill_files_and_manifest_records_are_complete(self) -> None:
        manifest = load_manifest(REPO)
        assets = {
            asset["id"]: asset
            for asset in manifest["assets"]
            if asset["kind"] == "skill"
        }
        cases = json.loads(FORWARD_CASES.read_text(encoding="utf-8"))["cases"]
        for case in cases:
            skill_id = case["skill"]
            asset = assets[skill_id]
            skill_path = REPO / f"skills/{skill_id}/SKILL.md"
            workflow_path = REPO / f"workflows/{skill_id}/WORKFLOW.md"
            self.assertTrue(skill_path.is_file())
            self.assertTrue(workflow_path.is_file())
            self.assertIn(f"skills/{skill_id}/SKILL.md", asset["files"])
            self.assertIn(f"workflows/{skill_id}/WORKFLOW.md", asset["files"])
            skill_text = skill_path.read_text(encoding="utf-8")
            workflow_text = workflow_path.read_text(encoding="utf-8")
            self.assertTrue(
                any(marker in skill_text for marker in ("Do not", "Reject", "must not"))
            )
            combined_text = skill_text + workflow_text
            self.assertTrue(
                "verif" in combined_text.casefold()
                or "check" in combined_text.casefold()
                or "evidence" in combined_text.casefold()
            )
            private_markers = ("/" + "Users/", "/" + "home/", "~" + "/", "." + "env")
            self.assertTrue(all(marker not in combined_text for marker in private_markers))

    def test_consequence_closure_keeps_mapping_and_completion_distinct(self) -> None:
        skill = (
            REPO / "skills/consequence-closure/SKILL.md"
        ).read_text(encoding="utf-8")
        workflow = (
            REPO / "workflows/consequence-closure/WORKFLOW.md"
        ).read_text(encoding="utf-8")
        template = (REPO / "templates/AGENTS.md").read_text(encoding="utf-8")

        for disposition in (
            "required",
            "conditional",
            "leverage",
            "optional",
            "blocked",
        ):
            self.assertIn(f"`{disposition}`", skill)
        for promotion in ("strengthen", "companion", "reference", "defer", "exclude"):
            self.assertIn(f"`{promotion}`", skill)
        self.assertIn("whole owning feature", skill)
        self.assertIn("impact receipt", skill)
        self.assertIn("pre-edit advisory discovery", workflow)
        self.assertIn("exact blocker or next promotion gate", workflow)
        self.assertIn("Provenance alone\nis not a disposition", workflow)
        self.assertIn("`Pre-existing` and `unrelated` describe", skill)
        self.assertIn("`consequence-closure` skill", template)

    def test_consequence_closure_dispositions_required_validation_failures(self) -> None:
        payload = json.loads(VALIDATION_FAILURE_CASES.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["skill"], "consequence-closure")
        cases = {case["id"]: case for case in payload["cases"]}
        self.assertEqual(
            cases["clear-local-stale-expectation"]["expected_action"],
            "fix-and-rerun-required-gate",
        )
        self.assertEqual(
            cases["unsafe-or-other-owned-failure"]["expected_action"],
            "preserve-name-blocker-and-mark-partial",
        )
        self.assertEqual(
            cases["ambiguous-product-contract"]["expected_action"],
            "inspect-owner-then-request-direction-or-report-unknown",
        )
        for case in cases.values():
            self.assertTrue(case["scenario"])
            self.assertTrue(case["must_not"])

        manifest = load_manifest(REPO)
        asset = next(
            item for item in manifest["assets"]
            if item["id"] == "consequence-closure"
        )
        fixture_path = (
            "fixtures/consequence-closure/validation-failure-disposition.json"
        )
        self.assertIn(fixture_path, asset["files"])
        self.assertEqual(
            asset["install"]["path_map"][fixture_path],
            "references/validation-failure-disposition.json",
        )


if __name__ == "__main__":
    unittest.main()
