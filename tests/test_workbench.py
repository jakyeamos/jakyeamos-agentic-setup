from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import cast

from scripts.catalog_validation import validate_manifest, validate_supplied_asset_snapshot
from scripts.catalog_index import order_collection_assets
from scripts.public_safety_check import scan_repository

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
REPO = SCRIPTS.parent
WORKBENCH = SCRIPTS / "workbench.py"


class WorkbenchCliTests(unittest.TestCase):
    def test_collection_order_follows_taxonomy_type_then_entry_id(self) -> None:
        taxonomy = {
            "types": [{"id": "skill"}, {"id": "workflow"}],
            "kind_defaults": {"skill": "skill", "workflow": "workflow"},
        }
        assets = [
            {"id": "zeta", "kind": "skill", "entry": {"type": "skill"}},
            {"id": "beta", "kind": "workflow", "entry": {"type": "workflow"}},
            {"id": "alpha", "kind": "skill", "entry": {"type": "skill"}},
        ]
        self.assertEqual(
            [asset["id"] for asset in order_collection_assets(assets, taxonomy)],
            ["alpha", "zeta", "beta"],
        )

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(WORKBENCH), *arguments],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_list_and_search_are_deterministic_json(self) -> None:
        first = self.run_cli("list", "--json")
        second = self.run_cli("list", "--json")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        payload = json.loads(first.stdout)
        ids = [asset["id"] for asset in payload["assets"]]
        self.assertEqual(ids, sorted(ids))

        search = self.run_cli("search", "--query", "long context", "--json")
        self.assertEqual(search.returncode, 0)
        self.assertEqual(
            [asset["id"] for asset in json.loads(search.stdout)["assets"]],
            ["context-budget-governor"],
        )

    def test_entry_projection_filters_and_collections(self) -> None:
        skills = self.run_cli("list", "--type", "skill", "--json")
        self.assertEqual(skills.returncode, 0)
        skills_payload = json.loads(skills.stdout)
        self.assertEqual(skills_payload["count"], 18)
        self.assertTrue(
            all(asset["entry"]["type"] == "skill" for asset in skills_payload["assets"])
        )

        safety = self.run_cli("list", "--topic", "safety", "--json")
        self.assertEqual(safety.returncode, 0)
        safety_payload = json.loads(safety.stdout)
        self.assertTrue(safety_payload["assets"])
        self.assertTrue(
            all("safety" in asset["entry"]["topics"] for asset in safety_payload["assets"])
        )

        featured = self.run_cli("list", "--featured", "--json")
        self.assertEqual(featured.returncode, 0)
        self.assertEqual(
            [asset["id"] for asset in json.loads(featured.stdout)["assets"]],
            [
                "consequence-closure",
                "repo-aware-context",
                "research-domain-writing",
                "safe-tool-guards",
            ],
        )

        unknown = self.run_cli("list", "--type", "not-a-type", "--json")
        self.assertEqual(unknown.returncode, 2)
        self.assertIn("unknown entry type", unknown.stderr)

    def test_generated_index_matches_canonical_catalog(self) -> None:
        checked = self.run_cli("index", "--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        rendered = self.run_cli("index")
        self.assertEqual(rendered.returncode, 0)
        self.assertEqual(
            rendered.stdout,
            (REPO / "catalog/index.md").read_text(encoding="utf-8"),
        )

    def test_show_and_install_preserve_the_target_boundary(self) -> None:
        shown = self.run_cli("show", "context-budget-governor", "--json")
        self.assertEqual(shown.returncode, 0)
        self.assertEqual(json.loads(shown.stdout)["id"], "context-budget-governor")
        self.assertEqual(json.loads(shown.stdout)["entry"]["type"], "playbook")

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            dry_run = self.run_cli(
                "install",
                "context-budget-governor",
                "--target",
                "codex",
                "--root",
                str(target),
                "--dry-run",
                "--json",
            )
            self.assertEqual(dry_run.returncode, 0)
            self.assertFalse(target.exists())
            self.assertTrue(json.loads(dry_run.stdout)["dry_run"])

            applied = self.run_cli(
                "install",
                "context-budget-governor",
                "--target",
                "codex",
                "--root",
                str(target),
                "--apply",
                "--json",
            )
            self.assertEqual(applied.returncode, 0)
            installed = (
                target / "workbench/workflows/context-budget-governor/WORKFLOW.md"
            )
            self.assertTrue(installed.is_file())
            original = installed.read_bytes()

            overwrite = self.run_cli(
                "install",
                "context-budget-governor",
                "--target",
                "codex",
                "--root",
                str(target),
                "--apply",
                "--json",
            )
            self.assertEqual(overwrite.returncode, 1)
            self.assertEqual(installed.read_bytes(), original)

    def test_consequence_closure_installs_validation_reference_into_clean_room(
        self,
    ) -> None:
        source = REPO / "fixtures/consequence-closure/validation-failure-disposition.json"
        expected_install_files = {
            "skills/consequence-closure/SKILL.md",
            "skills/consequence-closure/WORKFLOW.md",
            "skills/consequence-closure/references/validation-failure-disposition.json",
        }
        expected_files = {
            *expected_install_files,
            ".workbench-receipts/consequence-closure.json",
        }

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "clean-room-target"
            dry_run = self.run_cli(
                "install",
                "consequence-closure",
                "--target",
                "generic",
                "--root",
                str(target),
                "--dry-run",
                "--json",
            )
            self.assertEqual(dry_run.returncode, 0)
            self.assertFalse(target.exists())
            dry_payload = json.loads(dry_run.stdout)
            self.assertTrue(dry_payload["dry_run"])
            self.assertEqual(
                {
                    Path(action["destination"])
                    .resolve()
                    .relative_to(target.resolve())
                    .as_posix()
                    for action in dry_payload["actions"]
                },
                expected_install_files,
            )

            applied = self.run_cli(
                "install",
                "consequence-closure",
                "--target",
                "generic",
                "--root",
                str(target),
                "--apply",
                "--json",
            )
            self.assertEqual(applied.returncode, 0)
            applied_payload = json.loads(applied.stdout)
            self.assertFalse(applied_payload["dry_run"])
            self.assertTrue(all(action["status"] == "copied" for action in applied_payload["actions"]))

            installed = target / "skills/consequence-closure/references/validation-failure-disposition.json"
            self.assertEqual(installed.read_bytes(), source.read_bytes())
            self.assertEqual(
                {
                    path.relative_to(target).as_posix()
                    for path in target.rglob("*")
                    if path.is_file()
                },
                expected_files,
            )

    def test_uninstall_is_receipt_scoped_and_preserves_modified_or_unrelated_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "recovery-target"
            applied = self.run_cli(
                "install",
                "safe-tool-guards",
                "--target",
                "generic",
                "--root",
                str(target),
                "--apply",
                "--json",
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            unrelated = target / "unrelated-user-file.txt"
            unrelated.write_text("keep me\n", encoding="utf-8")

            preview = self.run_cli(
                "uninstall",
                "safe-tool-guards",
                "--target",
                "generic",
                "--root",
                str(target),
                "--dry-run",
                "--json",
            )
            self.assertEqual(preview.returncode, 0, preview.stderr)
            preview_payload = json.loads(preview.stdout)
            self.assertEqual(preview_payload["status"], "ready")
            self.assertTrue(
                all(
                    action["status"] == "would-remove"
                    for action in preview_payload["actions"]
                )
            )
            self.assertTrue(unrelated.is_file())

            removed = self.run_cli(
                "uninstall",
                "safe-tool-guards",
                "--target",
                "generic",
                "--root",
                str(target),
                "--apply",
                "--json",
            )
            self.assertEqual(removed.returncode, 0, removed.stderr)
            removed_payload = json.loads(removed.stdout)
            self.assertEqual(removed_payload["status"], "uninstalled")
            self.assertTrue(unrelated.is_file())
            self.assertFalse(
                (target / "workbench/workflows/safe-tool-guards/CONTRACT.md").exists()
            )
            self.assertFalse(
                (target / ".workbench-receipts/safe-tool-guards.json").exists()
            )

            reapplied = self.run_cli(
                "install",
                "safe-tool-guards",
                "--target",
                "generic",
                "--root",
                str(target),
                "--apply",
                "--json",
            )
            self.assertEqual(reapplied.returncode, 0, reapplied.stderr)
            modified = target / "workbench/workflows/safe-tool-guards/CONTRACT.md"
            modified.write_text("user change\n", encoding="utf-8")
            blocked = self.run_cli(
                "uninstall",
                "safe-tool-guards",
                "--target",
                "generic",
                "--root",
                str(target),
                "--apply",
                "--json",
            )
            self.assertEqual(blocked.returncode, 1)
            blocked_payload = json.loads(blocked.stdout)
            self.assertEqual(blocked_payload["status"], "blocked-uninstall-safety")
            self.assertEqual(modified.read_text(encoding="utf-8"), "user change\n")
            self.assertTrue(
                (target / ".workbench-receipts/safe-tool-guards.json").is_file()
            )

    def test_adapter_staging_is_manual_and_external_references_do_not_copy(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "adapter-target"
            staged = self.run_cli(
                "install",
                "adapter-codex",
                "--target",
                "codex",
                "--root",
                str(target),
                "--apply",
                "--json",
            )
            self.assertEqual(staged.returncode, 0)
            staged_payload = json.loads(staged.stdout)
            self.assertEqual(staged_payload["install_mode"], "stage")
            self.assertIn("Review", staged_payload["manual_review"])
            self.assertTrue(
                (target / "workbench/adapters/codex/WORKBENCH.md").is_file()
            )

            reference_target = Path(directory) / "reference-target"
            reference = self.run_cli(
                "install",
                "reference-aios",
                "--target",
                "generic",
                "--root",
                str(reference_target),
                "--apply",
                "--json",
            )
            self.assertEqual(reference.returncode, 0)
            self.assertEqual(json.loads(reference.stdout)["status"], "manual-review")
            self.assertFalse(reference_target.exists())

    def test_external_reference_map_is_linked_without_installable_runtime(self) -> None:
        manifest = json.loads(
            (REPO / "catalog/manifest.json").read_text(encoding="utf-8")
        )
        assets = {asset["id"]: asset for asset in manifest["assets"]}
        expected_links = {
            "reference-tmcp": "https://github.com/jakyeamos/tmcp",
            "reference-pronto": "https://github.com/jakyeamos/pronto",
            "reference-pre-cr-suite": "https://github.com/jakyeamos/pre-cr-suite",
            "reference-quality-runner": "https://github.com/jakyeamos/quality-runner",
        }
        for asset_id, link in expected_links.items():
            asset = assets[asset_id]
            self.assertEqual(asset["asset_class"], "external")
            self.assertEqual(asset["install"]["mode"], "manual")
            self.assertEqual(asset["external_links"], [link])

        self.assertTrue(
            (REPO / "docs/adoption-guide.md").is_file()
        )
        self.assertTrue(
            (REPO / "docs/workflow-multipliers/documentation-as-principles.md").is_file()
        )

    def test_catalog_validation_reports_duplicate_and_unsupported_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "catalog").mkdir()
            (root / "library").mkdir()
            (root / "catalog/taxonomy.json").write_text(
                (REPO / "catalog/taxonomy.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (root / "payload.md").write_text("payload\n", encoding="utf-8")
            (root / "bad.md").write_text(
                "[broken](missing-link.md)\n", encoding="utf-8"
            )
            asset = {
                "id": "sample-asset",
                "kind": "workflow",
                "asset_class": "portable",
                "title": "Sample",
                "summary": "Sample asset",
                "maturity": "stable",
                "capabilities": ["sample"],
                "supported_targets": ["generic"],
                "entrypoints": ["payload.md"],
                "files": ["bad.md", "missing.txt", "payload.md"],
                "dependencies": [],
                "provenance": {
                    "status": "authored",
                    "source": "authored-in-this-repository",
                    "license_status": "MIT",
                    "redistribution": "allowed",
                },
                "evidence": ["payload.md"],
                "install": {"mode": "copy", "destination": "sample"},
                "editorial": {"type": "unknown", "topics": ["Bad Topic"]},
            }
            manifest = {
                "schema_version": 1,
                "workbench": {
                    "id": "portable-agentic-workbench",
                    "name": "Portable Agentic Workbench",
                    "repository": "sample",
                    "version": "0.2.0",
                    "license": "MIT",
                },
                "asset_policy": {
                    name: name
                    for name in (
                        "portable",
                        "adapter",
                        "case-study",
                        "external",
                        "excluded",
                    )
                },
                "source_map": [
                    {"source_id": "sample", "class": "portable", "treatment": "sample"}
                ],
                "assets": [copy.deepcopy(asset), copy.deepcopy(asset)],
            }
            manifest_assets = cast(list[dict[str, object]], manifest["assets"])
            manifest_assets[1]["supported_targets"] = ["unknown"]
            manifest_assets[1]["provenance"] = {
                "status": "untrusted",
                "source": "authored-in-this-repository",
                "license_status": "MIT",
                "redistribution": "allowed",
            }
            (root / "catalog/manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            errors = validate_manifest(root)
            self.assertTrue(any("duplicate id" in error for error in errors))
            self.assertTrue(any("unsupported target" in error for error in errors))
            self.assertTrue(any("missing file" in error for error in errors))
            self.assertTrue(any("broken local link" in error for error in errors))
            self.assertTrue(
                any("invalid provenance status" in error for error in errors)
            )
            self.assertTrue(any("editorial type" in error for error in errors))
            self.assertTrue(any("lowercase slugs" in error for error in errors))

    def test_supplied_asset_snapshot_reports_independent_boundary_failures(self) -> None:
        result = validate_supplied_asset_snapshot(
            {
                "provenance": {"source": "/private/team/catalog-entry"},
                "editorial": {"type": "unknown-type"},
                "install": {"mode": "magic"},
            },
            {"setup", "workflow"},
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(
            result["checks"],
            {
                "private_source": "fail",
                "editorial_type": "fail",
                "installation_mode": "fail",
            },
        )
        self.assertEqual(len(result["errors"]), 3)
        self.assertTrue(result["unknown_checks"])

    def test_public_safety_scans_tracked_or_unowned_compass_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = root / ".project-compass/evidence/proof.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({"schema": "compass-evidence/v1", "workspace": "/" + "Users/example/repo"}))
            self.assertTrue(scan_repository(root))
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / ".gitignore").write_text(".project-compass/evidence/\n")
            self.assertEqual(scan_repository(root), [])
            valid_receipt = receipt.read_text()
            receipt.write_text(valid_receipt.replace("compass-evidence/v1", "unknown/v1"))
            self.assertTrue(scan_repository(root))
            receipt.write_text(valid_receipt)
            subprocess.run(["git", "-C", str(root), "add", "-f", str(receipt)], check=True)
            self.assertTrue(scan_repository(root))

    def test_public_safety_scanner_rejects_unsafe_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "unsafe.txt").write_text(
                "path: "
                + "/"
                + "Users/example/private.txt"
                + "\n"
                + "Authorization: "
                + "Bearer "
                + "abc123456789"
                + "\n",
                encoding="utf-8",
            )
            environment_name = ".e" + "nv"
            (root / environment_name).write_text("placeholder", encoding="utf-8")
            findings = scan_repository(root)
            self.assertTrue(
                any("private absolute path" in finding for finding in findings)
            )
            self.assertTrue(
                any("raw authorization header" in finding for finding in findings)
            )
            self.assertTrue(any("environment file" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
