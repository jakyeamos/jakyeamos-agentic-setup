#!/usr/bin/env python3
"""Unit tests for the deterministic Project Compass helper."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from project_compass import (
    ContractError,
    answer_quiz,
    checkpoint,
    load_quiz,
    score_compass_family,
    score_contract,
    start_quiz,
    validate_contract,
    validate_quiz,
    validate_registry,
)


def _outcome(
    outcome_id: str,
    targets: list[str],
    maturity: int,
    confidence: str = "high",
) -> dict:
    return {
        "id": outcome_id,
        "name": outcome_id.replace("-", " ").title(),
        "targets": targets,
        "maturity": maturity,
        "confidence": confidence,
        "layers": {
            "intended": "required",
            "planned": "planned",
            "implemented": "present",
            "verified": "observed",
        },
        "evidence": [],
        "blockers": [],
    }


def _contract() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "revision": 1,
        "project": {
            "name": "Fixture",
            "identity": "A fixture product",
            "audience": "Testers",
            "core_loop": "Arrange, act, learn",
            "north_star": "A proven user outcome",
            "not_this": ["A task counter"],
        },
        "targets": {
            "mvp": {"definition": "One honest usable loop"},
            "complete_product": {"definition": "The ratified full experience"},
        },
        "pillars": [
            {
                "id": "core",
                "name": "Core",
                "outcomes": [
                    _outcome("usable-loop", ["mvp", "complete_product"], 100),
                    _outcome("polished-loop", ["complete_product"], 50),
                ],
            },
            {
                "id": "trust",
                "name": "Trust",
                "outcomes": [
                    _outcome("safe-use", ["mvp", "complete_product"], 50, "medium")
                ],
            },
        ],
        "source_layers": {
            "intended": [],
            "planned": [],
            "implemented": [],
            "verified": [],
        },
        "drift": [],
        "updated_at": now,
    }


def _continuity() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    source = {"ref": "thread:fixture", "observed_at": now}
    return {
        "schema_version": 1,
        "revision": 1,
        "commitments": [{
            "id": "preserve-core",
            "kind": "constraint",
            "statement": "Preserve the proven user loop.",
            "status": "active",
            "source": source,
        }],
        "reconciliations": [{
            "id": "reframe-one",
            "observed_at": now,
            "source": source,
            "classification": "corrective",
            "materiality": "high",
            "incoming": "Use the existing behavioral source.",
            "project_evidence": [{"ref": "behavioral-spec.md", "observed_at": now}],
            "preserved": ["The proven user loop."],
            "changed": ["The implementation path."],
            "contradicted": [],
            "deferred": [],
            "left_behind": [],
            "unknown": ["Whether the full evidence boundary is covered."],
            "disposition": "pending-question",
            "question": "Should the remaining evidence requirements stay active?",
        }],
        "updated_at": now,
    }


def _scoped_contract(compass_id: str, parent_id: str, parent_outcomes: list[str]) -> dict:
    contract = _contract()
    contract["project"]["name"] = compass_id.replace("-", " ").title()
    contract["project"]["identity"] = f"The {compass_id} subsystem"
    contract["scope"] = {
        "id": compass_id,
        "kind": "subsystem",
        "parent_id": parent_id,
        "purpose": f"Keep {compass_id} aligned with its parent outcome.",
        "boundary": f"Owns the {compass_id} subsystem boundary.",
        "non_goals": ["Redefining the product identity"],
        "parent_outcomes": parent_outcomes,
        "paths": [f"src/{compass_id}"],
    }
    return contract


def _registry(now: str) -> dict:
    return {
        "schema_version": 1,
        "root_id": "project",
        "compasses": [
            {
                "id": "project",
                "kind": "root",
                "path": "contract.json",
                "parent_id": None,
                "status": "active",
            },
            {
                "id": "playback",
                "kind": "subsystem",
                "path": "compasses/playback.json",
                "parent_id": "project",
                "status": "active",
            },
        ],
        "links": [
            {
                "id": "playback-project",
                "from": "playback",
                "to": "project",
                "kind": "shared-invariant",
                "status": "aligned",
                "summary": "Playback preserves the root listening outcome.",
            }
        ],
        "updated_at": now,
    }


class CompassTests(unittest.TestCase):
    def test_balances_pillars_before_targets(self) -> None:
        scores = score_contract(_contract())
        self.assertEqual(scores["mvp"]["progress_percent"], 75)
        self.assertEqual(scores["complete_product"]["progress_percent"], 63)

    def test_rejects_arbitrary_maturity(self) -> None:
        contract = _contract()
        contract["pillars"][0]["outcomes"][0]["maturity"] = 60
        with self.assertRaises(ContractError):
            validate_contract(contract)

    def test_rejects_malformed_evidence(self) -> None:
        contract = _contract()
        contract["pillars"][0]["outcomes"][0]["evidence"] = [
            {"ref": "README.md", "observed_at": "not-a-date"}
        ]
        with self.assertRaises(ContractError):
            validate_contract(contract)

    def test_validates_scoped_contract_metadata(self) -> None:
        contract = _scoped_contract("playback", "project", ["usable-loop"])
        validate_contract(contract)
        contract["scope"]["paths"] = ["../outside"]
        with self.assertRaises(ContractError):
            validate_contract(contract)

    def test_scores_scoped_compass_family_and_alignment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            compass_dir = repo / ".project-compass"
            (compass_dir / "compasses").mkdir(parents=True)
            now = datetime.now(timezone.utc).isoformat()
            root = _contract()
            child = _scoped_contract("playback", "project", ["usable-loop"])
            (compass_dir / "contract.json").write_text(
                json.dumps(root), encoding="utf-8"
            )
            (compass_dir / "compasses" / "playback.json").write_text(
                json.dumps(child), encoding="utf-8"
            )
            registry = _registry(now)
            (compass_dir / "compasses.json").write_text(
                json.dumps(registry), encoding="utf-8"
            )
            validate_registry(registry)
            scores = score_compass_family(repo)
            self.assertEqual(scores["root_id"], "project")
            self.assertIn("playback", scores["children"])
            self.assertEqual(scores["alignment"]["status"], "aligned")
            self.assertEqual(scores["coverage"]["child_compasses"], 1)
            registry["links"][0]["status"] = "unknown"
            (compass_dir / "compasses.json").write_text(
                json.dumps(registry), encoding="utf-8"
            )
            self.assertEqual(
                score_compass_family(repo)["alignment"]["status"], "unknown"
            )
            registry["links"] = []
            (compass_dir / "compasses.json").write_text(
                json.dumps(registry), encoding="utf-8"
            )
            alignment = score_compass_family(repo)["alignment"]
            self.assertEqual(alignment["status"], "unknown")
            self.assertEqual(alignment["unlinked_children"], ["playback"])

    def test_rejects_scoped_parent_cycle(self) -> None:
        registry = _registry(datetime.now(timezone.utc).isoformat())
        registry["compasses"][1]["parent_id"] = "playback"
        with self.assertRaises(ContractError):
            validate_registry(registry)

    def test_greenfield_quiz_is_available_without_a_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            status = start_quiz(
                repo,
                "greenfield",
                session_id="greenfield-project",
                now="2026-08-14T12:00:00+00:00",
            )
            self.assertEqual(status["next_question"]["id"], "purpose")
            self.assertTrue(status["draft_only"])
            answer_quiz(
                repo,
                "greenfield-project",
                "purpose",
                "A clear user outcome.",
                now="2026-08-14T12:01:00+00:00",
            )
            next_status = answer_quiz(
                repo,
                "greenfield-project",
                "audience",
                "People who need the outcome.",
                now="2026-08-14T12:02:00+00:00",
            )
            self.assertEqual(next_status["answered"], 2)
            self.assertEqual(next_status["next_question"]["id"], "core-loop")
            quiz = load_quiz(repo)
            for question in quiz["sessions"][0]["questions"][2:]:
                answer_quiz(
                    repo,
                    "greenfield-project",
                    question["id"],
                    "A considered answer.",
                    now="2026-08-14T12:03:00+00:00",
                )
            completed = load_quiz(repo)["sessions"][0]
            validate_quiz(load_quiz(repo))
            self.assertEqual(completed["status"], "complete")
            self.assertEqual(completed["answers"][-1]["status"], "explicit")

    def test_brownfield_quiz_can_start_without_a_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            status = start_quiz(
                repo,
                "brownfield",
                session_id="brownfield-project",
                now="2026-08-14T12:00:00+00:00",
            )
            self.assertEqual(status["scope_kind"], "root")
            skipped = answer_quiz(
                repo,
                "brownfield-project",
                "desired-purpose",
                "",
                now="2026-08-14T12:01:00+00:00",
            )
            self.assertEqual(skipped["answer_statuses"]["desired-purpose"], "skipped")

    def test_brownfield_quiz_uses_bounded_evidence_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            status = start_quiz(
                Path(directory),
                "brownfield",
                session_id="bounded-brownfield",
                now="2026-08-14T12:00:00+00:00",
            )
            prompts = {
                question["id"]: question["prompt"]
                for question in load_quiz(Path(directory))["sessions"][0]["questions"]
            }
            self.assertEqual(status["next_question"]["id"], "desired-purpose")
            self.assertIn("capability clusters", prompts["intentional-behavior"])
            self.assertIn("one correction", prompts["intentional-behavior"])
            self.assertIn("do not need to enumerate", prompts["historical-drift"])
            self.assertNotIn("Which current behaviors", prompts["intentional-behavior"])

    def test_quiz_can_use_a_bounded_question_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            status = start_quiz(
                repo,
                "brownfield",
                session_id="short-brownfield",
                question_ids=["desired-purpose", "preserve-or-change"],
                now="2026-08-14T12:00:00+00:00",
            )
            self.assertEqual(status["total_questions"], 2)
            self.assertEqual(status["next_question"]["id"], "desired-purpose")
            answer_quiz(
                repo,
                "short-brownfield",
                "desired-purpose",
                "A focused product outcome.",
                now="2026-08-14T12:01:00+00:00",
            )
            completed = answer_quiz(
                repo,
                "short-brownfield",
                "preserve-or-change",
                "Keep the focused outcome.",
                now="2026-08-14T12:02:00+00:00",
            )
            self.assertEqual(completed["status"], "complete")

            with self.assertRaises(ContractError):
                start_quiz(
                    repo,
                    "brownfield",
                    session_id="invalid-brownfield",
                    question_ids=["not-a-question"],
                    now="2026-08-14T12:03:00+00:00",
                )

    def test_subsystem_greenfield_quiz_can_start_before_child_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            status = start_quiz(
                repo,
                "greenfield",
                compass_id="playback",
                scope_kind="subsystem",
                session_id="greenfield-playback",
                now="2026-08-14T12:00:00+00:00",
            )
            self.assertEqual(status["scope_kind"], "subsystem")
            self.assertEqual(status["next_question"]["id"], "purpose")
            self.assertTrue(status["draft_only"])

    def test_subsystem_prompts_offer_bounded_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            start_quiz(
                repo,
                "greenfield",
                compass_id="playback",
                scope_kind="subsystem",
                session_id="bounded-playback",
                now="2026-08-14T12:00:00+00:00",
            )
            prompts = {
                question["id"]: question["prompt"]
                for question in load_quiz(repo)["sessions"][0]["questions"]
            }
            self.assertIn("surface the relevant parent outcomes", prompts["parent-outcome"])
            self.assertIn("one correction", prompts["responsibilities"])
            self.assertIn("material handoffs", prompts["interfaces"])
            self.assertNotIn("What are all", prompts["interfaces"])

    def test_subsystem_realignment_quiz_uses_child_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            compass_dir = repo / ".project-compass"
            (compass_dir / "compasses").mkdir(parents=True)
            now = datetime.now(timezone.utc).isoformat()
            (compass_dir / "contract.json").write_text(
                json.dumps(_contract()), encoding="utf-8"
            )
            (compass_dir / "compasses" / "playback.json").write_text(
                json.dumps(_scoped_contract("playback", "project", ["usable-loop"])),
                encoding="utf-8",
            )
            (compass_dir / "compasses.json").write_text(
                json.dumps(_registry(now)), encoding="utf-8"
            )
            status = start_quiz(
                repo,
                "realignment",
                compass_id="playback",
                session_id="realign-playback",
                now="2026-08-14T12:00:00+00:00",
            )
            self.assertEqual(status["scope_kind"], "subsystem")
            self.assertEqual(status["next_question"]["id"], "desired-change")
            answer = answer_quiz(
                repo,
                "realign-playback",
                "desired-change",
                "Keep playback focused.",
                status="tentative",
                now="2026-08-14T12:01:00+00:00",
            )
            self.assertEqual(answer["answer_statuses"]["desired-change"], "tentative")

    def test_validates_continuity_and_reports_pending_questions(self) -> None:
        from project_compass import continuity_status, validate_continuity

        continuity = _continuity()
        validate_continuity(continuity)
        status = continuity_status(continuity)
        self.assertEqual(status["counts"]["active_commitments"], 1)
        self.assertEqual(status["counts"]["pending_reconciliations"], 1)

    def test_rejects_pending_reconciliation_without_question(self) -> None:
        from project_compass import validate_continuity

        continuity = _continuity()
        continuity["reconciliations"][0]["question"] = ""
        with self.assertRaises(ContractError):
            validate_continuity(continuity)

    def test_rejects_supersession_with_wrong_classification(self) -> None:
        from project_compass import validate_continuity

        continuity = _continuity()
        continuity["reconciliations"][0]["disposition"] = "recorded-supersession"
        with self.assertRaises(ContractError):
            validate_continuity(continuity)

    def test_rejects_supersession_without_reason(self) -> None:
        from project_compass import validate_continuity

        continuity = _continuity()
        reconciliation = continuity["reconciliations"][0]
        reconciliation["classification"] = "superseding"
        reconciliation["disposition"] = "recorded-supersession"
        with self.assertRaises(ContractError):
            validate_continuity(continuity)

    def test_validate_command_checks_optional_continuity_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            compass_dir = repo / ".project-compass"
            compass_dir.mkdir()
            (compass_dir / "contract.json").write_text(
                json.dumps(_contract()), encoding="utf-8"
            )
            continuity = _continuity()
            continuity["reconciliations"][0]["question"] = ""
            (compass_dir / "continuity.json").write_text(
                json.dumps(continuity), encoding="utf-8"
            )
            from project_compass import _validate_repo

            with self.assertRaises(ContractError):
                _validate_repo(repo)

    def test_checkpoint_splits_delivery_and_scope_delta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            compass_dir = repo / ".project-compass"
            compass_dir.mkdir()
            contract = _contract()
            (compass_dir / "contract.json").write_text(
                json.dumps(contract), encoding="utf-8"
            )
            first = checkpoint(repo, "first")
            self.assertIsNone(first["targets"]["mvp"]["delta"]["total"])

            contract["revision"] = 2
            contract["pillars"][1]["outcomes"][0]["maturity"] = 75
            contract["pillars"][0]["outcomes"].append(
                _outcome("new-mvp-scope", ["mvp", "complete_product"], 0)
            )
            (compass_dir / "contract.json").write_text(
                json.dumps(contract), encoding="utf-8"
            )
            second = checkpoint(repo, "second")
            mvp_delta = second["targets"]["mvp"]["delta"]
            self.assertEqual(mvp_delta["delivery"], 13)
            self.assertEqual(mvp_delta["scope"], -25)
            self.assertEqual(mvp_delta["total"], -12)
            lines = (compass_dir / "checkpoints.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
