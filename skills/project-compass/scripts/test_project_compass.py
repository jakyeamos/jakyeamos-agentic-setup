#!/usr/bin/env python3
"""Unit tests for the deterministic Project Compass helper."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from project_compass import ContractError, checkpoint, score_contract, validate_contract


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
