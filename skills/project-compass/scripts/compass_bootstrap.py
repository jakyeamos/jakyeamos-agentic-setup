"""Assess usable intent links without confusing declarations with behavior proof."""
from compass_sources import read_json, reference


def behavior_inventory(repo, inventory):
    ref = (inventory or {}).get('behavior_ref')
    result = {'status': 'unknown', 'source_ref': ref, 'behaviors': [], 'reason': 'Behavior inventory is not declared'}
    if not ref:
        return result
    try:
        document = read_json(repo, ref)
        rows = document['behaviors']
        if not isinstance(rows, list) or len(rows) > 10000:
            raise ValueError('behaviors must be a bounded array')
        ids = [r['id'] for r in rows]
        if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
            raise ValueError('behavior IDs must be unique nonempty strings')
        return {**result, 'status': 'measured', 'behaviors': rows, 'reason': None}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {**result, 'status': 'invalid', 'reason': str(exc)}


def bootstrap_projection(repo, development, nodes, relationships, coverage):
    """Readiness is scoped traceability, never a semantic correctness score."""
    inventory = behavior_inventory(repo, development.get('inventory'))
    behaviors = {b['id']: b for b in inventory['behaviors']}
    assessments = []
    for node in nodes:
        rows = [r for r in development.get('bindings', []) if r['compass_id'] == node['id'] and r['authority'] == 'accepted']
        gaps = []
        if not node.get('valid') or node.get('status') != 'active' or not rows:
            gaps.append('accepted-intent-missing')
        if not node.get('purpose') or not node.get('outcomes'):
            gaps.append('purpose-or-outcomes-missing')
        if node.get('kind') == 'subsystem' and not node.get('parent_outcomes'):
            gaps.append('parent-outcomes-missing')
        if not node.get('constraints'):
            gaps.append('exclusions-missing')
        if inventory['status'] != 'measured':
            gaps.append('behavior-inventory-' + inventory['status'])
        trace = []
        for row in rows:
            if not row.get('outcomes') or not row.get('constraints') or not row.get('references'):
                gaps.append('binding-intent-links-missing:' + row['id'])
            if not row.get('behavior_ids'):
                gaps.append('binding-behaviors-missing:' + row['id'])
            for ref in row.get('references', []):
                if reference(repo, ref)['status'] != 'present':
                    gaps.append('canonical-reference-unavailable:' + row['id'])
            for proof in row.get('proof', []):
                if reference(repo, proof['oracle_ref'])['status'] != 'present':
                    gaps.append('proof-oracle-unavailable:' + proof['id'])
            for behavior_id in row.get('behavior_ids', []):
                behavior = behaviors.get(behavior_id, {})
                spec_ref = behavior.get('spec_ref')
                proof_ids = [p['id'] for p in row.get('proof', []) if behavior_id in p.get('behavior_ids', [])]
                if not behavior or not isinstance(spec_ref, str) or not spec_ref or reference(repo, spec_ref)['status'] != 'present':
                    gaps.append('behavior-spec-missing:' + behavior_id)
                if not proof_ids:
                    gaps.append('behavior-proof-missing:' + behavior_id)
                trace.append({'behavior_id': behavior_id, 'binding_id': row['id'], 'outcomes': row.get('outcomes', []),
                              'spec_ref': spec_ref, 'proof_ids': proof_ids})
        links = [l for l in relationships if node['id'] in (l.get('from'), l.get('to'))]
        if any(not l.get('valid') or l.get('status') != 'aligned' for l in links):
            gaps.append('handoff-unresolved')
        if not links and not any(r.get('handoff_review') for r in rows):
            gaps.append('handoff-review-missing')
        owned = {p for r in rows for p in r.get('paths', [])}
        if owned.intersection(coverage['ambiguous_paths']):
            gaps.append('ownership-ambiguous')
        if any(item['binding'] in {r['id'] for r in rows} for item in coverage['missing_paths']):
            gaps.append('implementation-path-missing')
        assessments.append({'compass_id': node['id'], 'status': 'incomplete' if gaps else 'linked',
                            'gaps': sorted(set(gaps)), 'behavior_trace': trace})
    return {'schema': 'compass-bootstrap/v1', 'subsystems': assessments,
            'status': 'linked' if assessments and all(a['status'] == 'linked' for a in assessments)
                      and coverage['status'] == 'measured' and not coverage['unmapped_paths']
                      and inventory['status'] == 'measured' and not coverage['unmapped_behaviors'] else 'incomplete',
            'verification': 'Linked intent requires reviewed behavior oracles and current proof; structure alone cannot establish semantic preservation.'}
