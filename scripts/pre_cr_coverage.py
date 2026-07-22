#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import trace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
VALIDATORS = (
    ROOT / "scripts" / "validate_skills.py",
    ROOT / "scripts" / "validate_prevention_pack.py",
)
COVERAGE_PATH = ROOT / ".pre-cr" / "coverage.lcov"
COVERED_FILES = (
    ROOT / "scripts" / "validate_skills.py",
    ROOT / "scripts" / "validate_prevention_pack.py",
    ROOT / "scripts" / "catalog_validation.py",
    ROOT / "scripts" / "public_safety_check.py",
    ROOT / "scripts" / "validate_catalog.py",
    ROOT / "scripts" / "workbench.py",
)


def _executable_lines(source_file: Path) -> set[int]:
    return {
        line_number
        for line_number, line in enumerate(
            source_file.read_text(encoding="utf-8").splitlines(),
            start=1,
        )
        if line.strip() and not line.lstrip().startswith("#")
    }


def _run_validator() -> None:
    old_argv = sys.argv[:]
    try:
        for validator in VALIDATORS:
            sys.argv = [str(validator)]
            exec(
                compile(validator.read_text(encoding="utf-8"), str(validator), "exec"),
                {"__name__": "__main__", "__file__": str(validator)},
            )
    finally:
        sys.argv = old_argv


def _run_workbench_smoke() -> None:
    """Exercise public command paths inside the trace process."""

    from scripts import (
        public_safety_check,
        validate_catalog,
        validate_prevention_pack,
        workbench,
    )

    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        if validate_catalog.main() != 0:
            raise RuntimeError("catalog validation failed during coverage smoke")
        if public_safety_check.main(["--root", str(ROOT)]) != 0:
            raise RuntimeError("public safety failed during coverage smoke")
        if validate_prevention_pack.main(["--root", str(ROOT)]) != 0:
            raise RuntimeError("prevention-pack validation failed during coverage smoke")
        commands = (
            ["list", "--json"],
            ["search", "--query", "long context", "--json"],
            ["show", "context-budget-governor", "--json"],
        )
        for command in commands:
            if workbench.main(command) != 0:
                raise RuntimeError(f"workbench smoke failed: {command}")
        with tempfile.TemporaryDirectory() as directory:
            command = [
                "install",
                "context-budget-governor",
                "--target",
                "generic",
                "--root",
                str(Path(directory) / "target"),
                "--dry-run",
                "--json",
            ]
            if workbench.main(command) != 0:
                raise RuntimeError("workbench install smoke failed")


def _write_lcov(results: trace.CoverageResults) -> None:
    counts = results.counts
    COVERAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ["TN:jakyeamos-agent-skills"]
    for source_file in COVERED_FILES:
        executable_lines = _executable_lines(source_file)
        lines.append(f"SF:{source_file.relative_to(ROOT).as_posix()}")
        for line_number in sorted(executable_lines):
            hit_count = counts.get((str(source_file), line_number), 0)
            lines.append(f"DA:{line_number},{hit_count}")
        lines.append(f"LF:{len(executable_lines)}")
        lines.append(
            f"LH:{sum(1 for line_number in executable_lines if counts.get((str(source_file), line_number), 0) > 0)}"
        )
        lines.append("end_of_record")
    COVERAGE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    tracer = trace.Trace(
        count=True, trace=False, ignoredirs=[sys.base_prefix, sys.base_exec_prefix]
    )
    exit_code = 0
    try:
        tracer.runfunc(_run_validator)
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    try:
        tracer.runfunc(_run_workbench_smoke)
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    _write_lcov(tracer.results())
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
