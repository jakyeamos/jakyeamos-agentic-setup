from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
REPO = SCRIPTS.parent
WORKBENCH = SCRIPTS / "workbench.py"
sys.path.insert(0, str(SCRIPTS))

from catalog_validation import validate_manifest
from public_safety_check import scan_repository


class WorkbenchCliTests(unittest.TestCase):
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

    def test_show_and_install_preserve_the_target_boundary(self) -> None:
        shown = self.run_cli("show", "context-budget-governor", "--json")
        self.assertEqual(shown.returncode, 0)
        self.assertEqual(json.loads(shown.stdout)["id"], "context-budget-governor")

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
            installed = target / "workbench/workflows/context-budget-governor/WORKFLOW.md"
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

    def test_catalog_validation_reports_duplicate_and_unsupported_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "catalog").mkdir()
            (root / "payload.md").write_text("payload\n", encoding="utf-8")
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
                "files": ["payload.md"],
                "dependencies": [],
                "provenance": {
                    "status": "authored",
                    "source": "authored-in-this-repository",
                    "license_status": "MIT",
                    "redistribution": "allowed",
                },
                "evidence": ["payload.md"],
                "install": {"mode": "copy", "destination": "sample"},
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
                "asset_policy": {name: name for name in ("portable", "adapter", "case-study", "external", "excluded")},
                "source_map": [
                    {"source_id": "sample", "class": "portable", "treatment": "sample"}
                ],
                "assets": [copy.deepcopy(asset), copy.deepcopy(asset)],
            }
            manifest["assets"][1]["supported_targets"] = ["unknown"]
            (root / "catalog/manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            errors = validate_manifest(root)
            self.assertTrue(any("duplicate id" in error for error in errors))
            self.assertTrue(any("unsupported target" in error for error in errors))

    def test_public_safety_scanner_rejects_unsafe_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "unsafe.txt").write_text(
                "path: " + "/" + "Users/example/private.txt" + "\n"
                + "Authorization: " + "Bearer " + "abc123456789" + "\n",
                encoding="utf-8",
            )
            environment_name = ".e" + "nv"
            (root / environment_name).write_text("placeholder", encoding="utf-8")
            findings = scan_repository(root)
            self.assertTrue(any("private absolute path" in finding for finding in findings))
            self.assertTrue(any("raw authorization header" in finding for finding in findings))
            self.assertTrue(any("environment file" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
