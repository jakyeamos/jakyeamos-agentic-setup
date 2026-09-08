"""Advisory modernization disposition using existing remediation identities."""
from __future__ import annotations

from pathlib import Path

from compass_change import change_context

DISPOSITIONS = {"worthwhile_now", "alongside_planned_work", "deferred", "not_applicable", "insufficient_evidence"}


def assess(repo: Path, proposal: dict) -> dict:
    if not isinstance(proposal, dict) or proposal.get("schema") != "compass-modernization-proposal/v1":
        raise ValueError("unsupported modernization proposal")
    context = change_context(repo, paths=proposal.get("paths", []), compass_ids=proposal.get("compass_ids", []),
                             base=proposal.get("base_revision", "HEAD"))
    reasons = []
    if proposal.get("applicable") is False:
        disposition = "not_applicable"
        reasons.append(proposal.get("applicability_reason") or "Proposal is explicitly inapplicable.")
    elif proposal.get("defer_reason"):
        disposition = "deferred"
        reasons.append(proposal["defer_reason"])
    else:
        required = ("problem", "expected_benefit", "applicability_reason", "evidence_refs", "rollback", "remediation_id")
        missing = [key for key in required if not proposal.get(key)]
        if proposal.get("applicable") is not True:
            missing.append("explicit applicability")
        if missing or context["blockers"]:
            disposition = "insufficient_evidence"
            reasons = (["Missing: " + ", ".join(missing)] if missing else []) + ["Resolve affected intent and context blockers."]
        else:
            from compass_sources import reference
            unresolved = [ref for ref in proposal["evidence_refs"] if reference(repo, ref)["status"] != "present"]
            if unresolved:
                disposition = "insufficient_evidence"
                reasons = ["Unverified problem/benefit evidence: " + ", ".join(unresolved)]
            else:
                disposition = "alongside_planned_work" if proposal.get("planned_work_ref") else "worthwhile_now"
                reasons = [proposal["applicability_reason"]]
    return {"schema": "compass-modernization-assessment/v1", "disposition": disposition, "reasons": reasons,
            "problem": proposal.get("problem"), "expected_benefit": proposal.get("expected_benefit"),
            "remediation_id": proposal.get("remediation_id"), "trigger": proposal.get("trigger"),
            "affected_outcomes": [{"binding": b["id"], "outcomes": b["outcomes"]} for b in context["bindings"]],
            "preserved_constraints": context["contracts"] + context["bindings"],
            "required_evidence": context["required_proof"], "rollback": proposal.get("rollback"),
            "context_blockers": context["blockers"], "execution_authority": False, "implementation_work": [],
            "source": context["source"], "base_revision": context["base_revision"]}
