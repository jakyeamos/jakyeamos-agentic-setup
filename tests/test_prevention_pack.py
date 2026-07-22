from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_prevention_pack import (
    REQUIRED_ASSETS,
    SUPPORTED_TARGETS,
    WORKFLOW_MARKERS,
    validate_prevention_pack,
)


REPO = Path(__file__).resolve().parents[1]


class PreventionPackTests(unittest.TestCase):
    def test_shared_prevention_pack_is_valid(self) -> None:
        self.assertEqual(validate_prevention_pack(REPO), [])

    def test_missing_contract_marker_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative, markers in WORKFLOW_MARKERS.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n".join(markers), encoding="utf-8")

            assets = []
            for asset_id, files in REQUIRED_ASSETS.items():
                assets.append(
                    {
                        "id": asset_id,
                        "kind": "workflow",
                        "files": list(files),
                        "supported_targets": sorted(SUPPORTED_TARGETS),
                        "evidence": ["evidence.md"],
                        "validation": [
                            "python3 scripts/validate_prevention_pack.py"
                        ],
                        "install": {
                            "mode": "copy",
                            "manual_review": "Review before enabling.",
                        },
                    }
                )
            (root / "catalog").mkdir()
            (root / "catalog/manifest.json").write_text(
                json.dumps({"assets": assets}), encoding="utf-8"
            )

            target = root / "workflows/repo-aware-context/WORKFLOW.md"
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    WORKFLOW_MARKERS[target.relative_to(root).as_posix()][0], ""
                ),
                encoding="utf-8",
            )
            errors = validate_prevention_pack(root)
            self.assertIn(
                "workflows/repo-aware-context/WORKFLOW.md: missing prevention marker identity and freshness gate",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
