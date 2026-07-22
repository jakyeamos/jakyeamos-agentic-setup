from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.catalog_validation import load_manifest


REPO = Path(__file__).resolve().parents[1]
FORWARD_CASES = REPO / "fixtures/forward-tests.json"


class PromotedSkillTests(unittest.TestCase):
    def test_each_promoted_skill_has_trigger_and_non_trigger_forward_cases(self) -> None:
        payload = json.loads(FORWARD_CASES.read_text(encoding="utf-8"))
        cases = payload["cases"]
        self.assertEqual(len(cases), 9)
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


if __name__ == "__main__":
    unittest.main()
