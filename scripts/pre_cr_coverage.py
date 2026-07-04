#!/usr/bin/env python3
from __future__ import annotations

import sys
import trace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skills.py"
COVERAGE_PATH = ROOT / ".pre-cr" / "coverage.lcov"


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
    sys.argv = [str(VALIDATOR)]
    try:
        exec(
            compile(VALIDATOR.read_text(encoding="utf-8"), str(VALIDATOR), "exec"),
            {"__name__": "__main__", "__file__": str(VALIDATOR)},
        )
    finally:
        sys.argv = old_argv


def _write_lcov(results: trace.CoverageResults) -> None:
    counts = results.counts
    executable_lines = _executable_lines(VALIDATOR)
    COVERAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ["TN:jakyeamos-agent-skills", f"SF:{VALIDATOR.relative_to(ROOT).as_posix()}"]
    for line_number in sorted(executable_lines):
        hit_count = counts.get((str(VALIDATOR), line_number), 0)
        lines.append(f"DA:{line_number},{hit_count}")
    lines.append(f"LF:{len(executable_lines)}")
    lines.append(
        f"LH:{sum(1 for line_number in executable_lines if counts.get((str(VALIDATOR), line_number), 0) > 0)}"
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
    _write_lcov(tracer.results())
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
