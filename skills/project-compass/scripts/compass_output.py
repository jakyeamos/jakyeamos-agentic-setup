"""Lossless packet artifacts and bounded presentation of fully evaluated gates."""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path

PACKET_LIMIT = 32768
ARTIFACT_LIMIT = 1024 * 1024


def canonical_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_packet(repo: Path, destination: Path, result: dict) -> dict:
    """Create a complete entry artifact without clobbering or following links."""
    if result.get("phase") != "entry" or result.get("eligible") is not True:
        raise ValueError("Packet artifacts require an eligible entry context")
    payload = canonical_bytes(result)
    if len(payload) > ARTIFACT_LIMIT:
        raise ValueError("Complete packet artifact exceeds 1 MiB; select a smaller scope")
    destination = destination if destination.is_absolute() else repo / destination
    try:
        parts = destination.relative_to(repo).parts
    except ValueError as exc:
        raise ValueError("Packet output must be inside workspace .quality-runner/compass/") from exc
    if len(parts) < 3 or parts[:2] != (".quality-runner", "compass") or ".." in parts:
        raise ValueError("Packet output must be inside workspace .quality-runner/compass/")
    descriptor_result = {"schema": "compass-packet-artifact/v1", "source": result["source"],
            "base_revision": result["base_revision"], "phase": "entry",
            "artifact_path": str(destination), "artifact_digest": hashlib.sha256(payload).hexdigest(),
            "artifact_bytes": len(payload), "affected_compasses": result["affected_compasses"],
            "eligible": True, "execution_authority": False,
            "instruction": "Inspect the complete artifact before explicitly adopting it as the prepared packet. This descriptor is not a prepared packet."}
    if len(canonical_bytes(descriptor_result)) > PACKET_LIMIT:
        raise ValueError("Artifact descriptor exceeds 32 KiB; select a smaller scope")
    # Directory descriptors keep the destination anchored even if a parent is renamed.
    descriptor = os.open(repo, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in parts[:-1]:
            try:
                os.mkdir(component, mode=0o700, dir_fd=descriptor)
            except FileExistsError:
                pass
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        fd = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=descriptor)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            os.unlink(parts[-1], dir_fd=descriptor)
            raise
    finally:
        os.close(descriptor)
    return descriptor_result


def gate_summary(result: dict, prepared_path: Path, prepared_bytes: bytes) -> dict:
    """Summarize presentation only; every blocker from the full producer survives."""
    return {"schema": "compass-gate-summary/v1", "source": result["source"],
            "base_revision": result["base_revision"], "phase": "completion",
            "eligible": result["eligible"], "execution_authority": False,
            "blockers": result["blockers"], "affected_compasses": result["affected_compasses"],
            "proof_status_counts": dict(Counter(p["status"] for p in result["required_proof"])),
            "prepared_path": str(prepared_path),
            "prepared_digest": hashlib.sha256(prepared_bytes).hexdigest(),
            "full_result_digest": hashlib.sha256(canonical_bytes(result)).hexdigest(),
            "full_result_bytes": len(canonical_bytes(result)), "detail_omitted": True,
            "drill_down": result["drill_down"],
            "detail_instruction": "Inspect the complete prepared artifact and referenced contracts; rerun gate for current full-diff eligibility. The summary cannot be adopted as an entry packet."}
