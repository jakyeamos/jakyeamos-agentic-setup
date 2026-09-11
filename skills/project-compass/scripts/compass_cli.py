"""CLI for the canonical Compass producers and legacy helper commands."""
from __future__ import annotations
import argparse
import json
import sys
import subprocess
from pathlib import Path
from typing import Any
from project_compass import (ContractError, QUIZ_MODES, COMPASS_KINDS, QUIZ_ANSWER_STATUSES,
    _validate_repo, _registry_path, score_compass_family, score_contract, continuity_status,
    load_continuity, start_quiz, answer_quiz, quiz_status, checkpoint)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "score"):
        child = subparsers.add_parser(command)
        child.add_argument("repo", type=Path)
        child.add_argument("--json", action="store_true")
    for command in ("family", "change-context", "assess", "prove", "gate"):
        child = subparsers.add_parser(command)
        child.add_argument("repo", type=Path)
        child.add_argument("--json", action="store_true")
        if command == "family":
            child.add_argument("--summary", action="store_true")
        elif command == "change-context":
            child.add_argument("--path", action="append", default=[])
            child.add_argument("--compass-id", action="append", default=[])
            child.add_argument("--base", default="HEAD")
            child.add_argument("--prepared", type=Path)
            child.add_argument("--completion", action="store_true")
            child.add_argument("--packet-output", type=Path)
            child.add_argument("--continue", dest="continuation", action="store_true")
        elif command == "gate":
            child.add_argument("--prepared", type=Path, default=Path(".quality-runner/compass/prepared.json"))
        elif command == "assess":
            child.add_argument("--proposal", type=Path, required=True)
        elif command == "prove":
            child.add_argument("--binding", required=True)
            child.add_argument("--proof", required=True)
    child = subparsers.add_parser("checkpoint")
    child.add_argument("repo", type=Path)
    child.add_argument("--note")
    child.add_argument("--json", action="store_true")
    child = subparsers.add_parser("continuity")
    child.add_argument("repo", type=Path)
    child.add_argument("--json", action="store_true")
    quiz = subparsers.add_parser("quiz")
    quiz_subparsers = quiz.add_subparsers(dest="quiz_command", required=True)
    start = quiz_subparsers.add_parser("start")
    start.add_argument("repo", type=Path)
    start.add_argument("--mode", choices=sorted(QUIZ_MODES), required=True)
    start.add_argument("--compass-id", default="project")
    start.add_argument("--scope-kind", choices=sorted(COMPASS_KINDS))
    start.add_argument("--session-id")
    start.add_argument(
        "--question-id",
        dest="question_ids",
        action="append",
        help="limit the session to selected question ids; repeat for multiple questions",
    )
    start.add_argument("--now")
    start.add_argument("--json", action="store_true")
    answer = quiz_subparsers.add_parser("answer")
    answer.add_argument("repo", type=Path)
    answer.add_argument("--session-id", required=True)
    answer.add_argument("--question-id", required=True)
    answer.add_argument("--value", default="")
    answer.add_argument("--status", choices=sorted(QUIZ_ANSWER_STATUSES), default="explicit")
    answer.add_argument("--source-ref", default="conversation:user")
    answer.add_argument("--now")
    answer.add_argument("--json", action="store_true")
    status = quiz_subparsers.add_parser("status")
    status.add_argument("repo", type=Path)
    status.add_argument("--session-id", required=True)
    status.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    validation_command = []
    if arguments and arguments[0] == "prove" and "--" in arguments:
        boundary = arguments.index("--")
        validation_command = arguments[boundary + 1:]
        arguments = arguments[:boundary]
    args = _parser().parse_args(arguments)
    try:
        repo = args.repo.resolve()
        if args.command == "family":
            from compass_projection import family_projection
            result = family_projection(repo)
            if args.summary:
                from compass_projection import family_summary
                result = family_summary(result)
        elif args.command == "gate":
            from compass_change import change_context
            packet_path = args.prepared if args.prepared.is_absolute() else repo / args.prepared
            if not packet_path.is_file():
                raise ValueError("Prepared Compass packet missing; prepare affected paths at task entry into .quality-runner/compass/prepared.json")
            prepared_bytes = packet_path.read_bytes()
            prepared = json.loads(prepared_bytes)
            if not isinstance(prepared, dict) or not isinstance(prepared.get("base_revision"), str):
                raise ValueError("Prepared Compass packet requires a base revision")
            result = change_context(repo, paths=[], compass_ids=prepared.get("direct_compasses", []),
                                    base=prepared["base_revision"], prepared=prepared, completion=True)
        elif args.command == "change-context":
            from compass_change import change_context
            prepared = json.loads(args.prepared.read_text()) if args.prepared else None
            result = change_context(repo, paths=args.path, compass_ids=args.compass_id,
                                    base=args.base, prepared=prepared, completion=args.completion, continuation=args.continuation)
            if args.packet_output:
                from compass_output import write_packet
                result = write_packet(repo, args.packet_output, result)
        elif args.command == "assess":
            from compass_assessment import assess
            if args.proposal.stat().st_size > 1024 * 1024:
                raise ValueError("Assessment proposal exceeds 1 MiB; select a smaller scope")
            result = assess(repo, json.loads(args.proposal.read_text()))
        elif args.command == "prove":
            from compass_change import prove
            result = prove(repo, args.binding, args.proof, validation_command)
        elif args.command == "validate":
            _validate_repo(repo)
            result: dict[str, Any] = {"valid": True}
        elif args.command == "score":
            data = _validate_repo(repo)
            result = (
                score_compass_family(repo)
                if _registry_path(repo).exists()
                else score_contract(data)
            )
        elif args.command == "continuity":
            result = continuity_status(load_continuity(repo))
        elif args.command == "quiz":
            if args.quiz_command == "start":
                result = start_quiz(
                    repo,
                    args.mode,
                    compass_id=args.compass_id,
                    session_id=args.session_id,
                    now=args.now,
                    scope_kind=args.scope_kind,
                    question_ids=args.question_ids,
                )
            elif args.quiz_command == "answer":
                result = answer_quiz(
                    repo,
                    args.session_id,
                    args.question_id,
                    args.value,
                    status=args.status,
                    source_ref=args.source_ref,
                    now=args.now,
                )
            else:
                result = quiz_status(repo, args.session_id)
        else:
            result = checkpoint(repo, args.note)
    except (ContractError, ValueError, OSError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        if getattr(args, "json", False):
            print(json.dumps({"valid": False, "error": str(exc)}))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1

    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.command in {"change-context", "gate"} and len(encoded.encode()) + 1 > 32768:
        encoded = json.dumps(result, separators=(",", ":"), sort_keys=True)
    if args.command == "gate" and len(encoded.encode()) + 1 > 32768:
        from compass_output import gate_summary
        result = gate_summary(result, packet_path, prepared_bytes)
        encoded = json.dumps(result, separators=(",", ":"), sort_keys=True)
    if args.command in {"change-context", "gate"} and len(encoded.encode()) + 1 > 32768:
        bounded = {k: result[k] for k in ("schema", "source", "base_revision", "phase", "drill_down")}
        bounded.update(affected_compasses=[], eligible=False, execution_authority=False,
                       blockers=[{"kind": "context-too-large", "action": "Select a narrower subsystem; use family for drill-down."}],
                       detail_omitted=True)
        print(json.dumps(bounded, indent=2, sort_keys=True))
        return 2
    print("valid" if args.command == "validate" and not args.json else encoded)
    if args.command in {"change-context", "gate"} and result["phase"] == "completion" and not result["eligible"]:
        return 2
    if args.command == "prove" and result["exit_code"]:
        return 2
    return 0
