"""Explicit decision assumptions and source-bound, declared assessment reviews."""
from compass_sources import digest, reference


def text(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value, minimum=1):
    return (isinstance(value, list) and minimum <= len(value) <= 100
            and all(text(v) for v in value) and len(value) == len(set(value)))


def validate_reasoning(value):
    if (not isinstance(value, dict) or value.get('schema') != 'compass-decision-reasoning/v1'
            or value.get('kind') not in ('outcome', 'constraint', 'implementation')
            or not isinstance(value.get('assumptions'), list) or len(value['assumptions']) > 50):
        raise ValueError('decision reasoning requires version, kind and bounded assumptions')
    seen = set()
    for row in value['assumptions']:
        if (not isinstance(row, dict) or not all(text(row.get(k)) for k in ('id', 'statement', 'reconsider_when'))
                or row['id'] in seen or not strings(row.get('evidence_refs'), 0)
                or row.get('status') not in ('supported', 'challenged', 'unknown')):
            raise ValueError('assumptions require unique IDs, evidence, status and reconsideration condition')
        if row['status'] == 'supported' and not row['evidence_refs']:
            raise ValueError('supported assumption requires evidence references')
        seen.add(row['id'])


def decision_refs(decision):
    return [ref for a in (decision or {}).get('reasoning', {}).get('assumptions', [])
            for ref in a['evidence_refs']]


def review_status(repo, review, subject, claims):
    """Validate recorded review completeness/freshness, never infer prose truth."""
    if review is None:
        return {'status': 'missing', 'reasons': ['An evidence-backed review is required.']}
    if (not isinstance(review, dict) or review.get('schema') != 'compass-assessment-review/v1'
            or not all(text(review.get(k)) for k in ('reviewer', 'source_ref', 'rationale'))
            or review.get('verdict') not in ('justified', 'retain', 'rejected', 'insufficient')):
        return {'status': 'invalid', 'reasons': ['Review requires version, reviewer, provenance, rationale and verdict.']}
    refs = reference(repo, review['source_ref'])
    if refs['status'] != 'present' or review.get('source_digest') != refs['digest']:
        return {'status': 'stale', 'reasons': ['Review provenance is missing or changed.']}
    if review.get('subject_digest') != subject:
        return {'status': 'stale', 'reasons': ['Proposal or affected source changed since review.']}
    rows = review.get('claims')
    if not isinstance(rows, dict) or set(rows) != set(claims):
        return {'status': 'invalid', 'reasons': ['Review must address: ' + ', '.join(claims)]}
    for name, row in rows.items():
        if (not isinstance(row, dict) or not text(row.get('rationale'))
                or row.get('finding') not in ('supported', 'contradicted', 'unknown')
                or not isinstance(row.get('evidence'), list) or not 1 <= len(row['evidence']) <= 30):
            return {'status': 'invalid', 'reasons': ['Incomplete evidence analysis for ' + name]}
        for item in row['evidence']:
            if not isinstance(item, dict) or not text(item.get('ref')):
                return {'status': 'invalid', 'reasons': ['Malformed review evidence.']}
            current = reference(repo, item['ref'])
            if current['status'] != 'present' or current['digest'] != item.get('digest'):
                return {'status': 'stale', 'reasons': ['Review evidence is missing or changed: ' + item['ref']]}
    return {'status': 'current', 'verdict': review['verdict'], 'reviewer': review['reviewer'],
            'claims_supported': all(r['finding'] == 'supported' for r in rows.values()),
            'rationale': review['rationale'], 'source_ref': review['source_ref'],
            'authority': 'declared-review-not-authenticated-approval', 'reasons': []}
