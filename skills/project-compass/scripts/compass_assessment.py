"""Advisory alternatives and declared review, separate from execution and proof."""
from pathlib import Path

from compass_change import binding_inputs, change_context
from compass_projection import family_projection
from compass_sources import bindings, digest, read_json, reference
from compass_review import decision_refs, review_status, strings, text

DISPOSITIONS = {'worthwhile_now', 'alongside_planned_work', 'deferred', 'not_applicable',
                'insufficient_evidence', 'retain_current_design', 'rejected'}
CLAIMS = ('problem', 'causal_fit', 'benefit', 'alternatives', 'preservation')


def alternatives(proposal, context):
    rows = proposal.get('alternatives')
    if not isinstance(rows, list) or not 3 <= len(rows) <= 12:
        return ['Compare delete, simplify and retain alternatives.'], []
    errors, ids, kinds = [], set(), set()
    outcomes = {o for b in context['bindings'] for o in b['outcomes']}
    for row in rows:
        if not isinstance(row, dict):
            errors.append('Alternative must be an object.')
            continue
        if not all(text(row.get(k)) for k in ('id', 'summary', 'consequences', 'consumer_impact', 'tradeoffs')):
            errors.append('Each alternative requires ID, summary, consequences, consumers and tradeoffs.')
        if not text(row.get('id')) or row.get('id') in ids:
            errors.append('Alternative IDs must be unique.')
        else:
            ids.add(row['id'])
        if row.get('kind') not in ('delete', 'simplify', 'retain', 'optimize', 'automate'):
            errors.append('Unknown alternative kind.')
        else:
            kinds.add(row['kind'])
        if not strings(row.get('outcome_ids')) or not set(row.get('outcome_ids', [])).issubset(outcomes):
            errors.append('Alternative must reference affected outcome IDs.')
        if not strings(row.get('evidence_refs')):
            errors.append('Alternative requires evidence references.')
    if not {'delete', 'simplify', 'retain'}.issubset(kinds):
        errors.append('Delete, simplify and retain must all be considered, including reasons to rule them out.')
    if not text(proposal.get('selected_alternative')) or proposal['selected_alternative'] not in ids:
        errors.append('Select an existing alternative ID.')
    return errors, rows


def follow_up(repo, observation, context, inputs):
    if observation is None:
        return {'status': 'not_recorded', 'benefit_realized': 'unknown'}
    try:
        if not isinstance(observation, dict) or observation.get('schema') != 'compass-benefit-observation/v1':
            raise ValueError('unsupported benefit observation')
        prior = read_json(repo, observation['assessment_ref'])
        if (digest(prior) != observation.get('assessment_digest')
                or prior.get('schema') != 'compass-modernization-assessment/v1'
                or prior.get('disposition') not in {'worthwhile_now', 'alongside_planned_work'}
                or prior.get('review', {}).get('status') != 'current'
                or prior.get('source', {}).get('repository') != context['source']['repository']
                or prior.get('source', {}).get('workspace') != context['source']['workspace']
                or prior.get('base_revision') != context['base_revision']):
            raise ValueError('follow-up requires the exact prior reviewed recommendation in this workspace/base')
        if not {b['binding'] for b in prior.get('affected_outcomes', [])}.issubset(inputs):
            raise ValueError('follow-up must include every originally affected binding')
        plan = prior.get('benefit_check', {})
        comparisons = observation.get('comparisons')
        if (not isinstance(comparisons, list) or not comparisons or len(comparisons) > 30
                or any(not isinstance(c, dict) or not all(text(c.get(k)) for k in
                       ('measure', 'before', 'after', 'interpretation')) or not strings(c.get('evidence_refs')) for c in comparisons)):
            raise ValueError('record before/after comparisons with evidence and interpretation')
        if {c['measure'] for c in comparisons} != set(plan.get('measures', [])) or len(comparisons) != len(plan.get('measures', [])):
            raise ValueError('comparisons must cover every promised measure exactly once')
        refs = {r: reference(repo, r) for c in comparisons for r in c['evidence_refs']}
        subject = digest({'observation': {k: v for k, v in observation.items() if k != 'review'},
                          'source': {k: context['source'][k] for k in ('repository', 'workspace')}, 'inputs': inputs, 'references': refs})
        review = review_status(repo, observation.get('review'), subject, ('attribution', 'measurement', 'preservation'))
        current = review['status'] == 'current' and review.get('claims_supported') and not context['blockers'] and all(r['status'] == 'present' for r in refs.values())
        if observation.get('result') not in {'realized', 'not_realized', 'mixed', 'unknown'}:
            raise ValueError('observation requires explicit benefit result')
        return {'status': 'reviewed' if current and review.get('verdict') == 'justified' else 'unverified',
                'benefit_realized': observation['result'] if current and review.get('verdict') == 'justified' else 'unknown',
                'expected_benefit': prior['expected_benefit'], 'benefit_check': plan,
                'comparisons': comparisons, 'review_target': subject, 'review': review,
                'preservation_proof': 'separate-completion-gate-required'}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {'status': 'invalid', 'benefit_realized': 'unknown', 'reason': str(exc)}


def assess(repo: Path, proposal: dict) -> dict:
    if not isinstance(proposal, dict) or proposal.get('schema') not in {'compass-modernization-proposal/v1', 'compass-modernization-proposal/v2'}:
        raise ValueError('unsupported modernization proposal')
    if not strings(proposal.get('paths', []), 0) or not strings(proposal.get('compass_ids', []), 0):
        raise ValueError('assessment selectors must be bounded string arrays')
    if not proposal.get('paths') and not proposal.get('compass_ids'):
        raise ValueError('assessment requires an explicit bounded scope')
    context = change_context(repo, paths=proposal.get('paths', []), compass_ids=proposal.get('compass_ids', []),
                             base=proposal.get('base_revision', 'HEAD'))
    family = family_projection(repo)
    nodes = {n.get('id'): n for n in family['nodes']}
    relevant = [b for b in bindings(repo)['bindings'] if b['id'] in {r['id'] for r in context['bindings']}]
    inputs = {b['id']: binding_inputs(repo, b, nodes) for b in relevant}
    errors, options = alternatives(proposal, context)
    if proposal['schema'].endswith('/v1'):
        errors.append('Legacy proposal is readable but requires v2 alternatives and review before recommendation.')
    required = ('problem', 'expected_benefit', 'applicability_reason', 'rollback', 'reconsider_when')
    errors += ['Missing: ' + k for k in required if not text(proposal.get(k))]
    selected = next((r for r in options if isinstance(r, dict) and r.get('id') == proposal.get('selected_alternative')), {})
    if selected.get('kind') != 'retain' and not text(proposal.get('remediation_id')):
        errors.append('Changes must reuse an existing remediation ID.')
    if proposal.get('applicable') is not True:
        errors.append('Explicit applicability is required.')
    plan = proposal.get('benefit_check')
    if (not isinstance(plan, dict) or not strings(plan.get('measures'))
            or not all(text(plan.get(k)) for k in ('baseline_ref', 'success_condition', 'method'))):
        errors.append('Define benefit measures, baseline reference, method and success condition.')
    refs = set(proposal.get('evidence_refs', [])) if strings(proposal.get('evidence_refs')) else set()
    if not refs:
        errors.append('Problem and benefit evidence references are required.')
    if 'planned_work_ref' in proposal:
        if text(proposal['planned_work_ref']):
            refs.add(proposal['planned_work_ref'])
        else:
            errors.append('Planned work requires a source reference.')
    for row in options:
        if isinstance(row, dict) and strings(row.get('evidence_refs')):
            refs.update(row['evidence_refs'])
    for decision in context['decisions']:
        refs.update(decision_refs(decision))
    if isinstance(plan, dict) and text(plan.get('baseline_ref')):
        refs.add(plan['baseline_ref'])
    evidence = {r: reference(repo, r) for r in sorted(refs)}
    errors += ['Missing or unverified evidence: ' + r for r, v in evidence.items() if v['status'] != 'present']
    if context['blockers']:
        errors.append('Resolve affected intent and context blockers.')
    subject = digest({'proposal': {k: v for k, v in proposal.items() if k not in {'review', 'observation'}},
                      'source': {k: context['source'][k] for k in ('repository', 'workspace')}, 'base_revision': context['base_revision'],
                      'inputs': inputs, 'decisions': context['decisions'], 'evidence': evidence})
    review = review_status(repo, proposal.get('review'), subject, CLAIMS)
    disposition, reasons = 'insufficient_evidence', errors + review['reasons']
    if proposal.get('applicable') is False:
        disposition, reasons = 'not_applicable', [proposal.get('applicability_reason') or 'Explicitly inapplicable.']
    elif text(proposal.get('defer_reason')):
        disposition, reasons = 'deferred', [proposal['defer_reason']]
    elif not errors and review['status'] == 'current':
        verdict = review['verdict']
        if verdict == 'rejected':
            disposition = 'rejected'
        elif review['claims_supported'] and verdict == 'retain' and selected.get('kind') == 'retain':
            disposition = 'retain_current_design'
        elif review['claims_supported'] and verdict == 'justified' and selected.get('kind') != 'retain':
            disposition = 'alongside_planned_work' if proposal.get('planned_work_ref') else 'worthwhile_now'
        reasons = [review['rationale']]
        if disposition == 'insufficient_evidence':
            reasons.append('Review claims or verdict do not justify the selected alternative.')
    return {'schema': 'compass-modernization-assessment/v1', 'review_contract': 'compass-assessment-review/v1',
            'disposition': disposition, 'reasons': reasons, 'proposal_complete': not errors,
            'review_target': subject, 'review': review, 'evidence': evidence,
            'problem': proposal.get('problem'), 'expected_benefit': proposal.get('expected_benefit'),
            'alternatives': options, 'selected_alternative': proposal.get('selected_alternative'),
            'decisions': context['decisions'], 'benefit_check': plan, 'reconsider_when': proposal.get('reconsider_when'),
            'benefit_observation': follow_up(repo, proposal.get('observation'), context, inputs),
            'remediation_id': proposal.get('remediation_id'), 'trigger': proposal.get('trigger'),
            'planned_work_ref': proposal.get('planned_work_ref'),
            'affected_outcomes': [{'binding': b['id'], 'outcomes': b['outcomes']} for b in context['bindings']],
            'preserved_constraints': context['contracts'] + context['bindings'],
            'required_evidence': context['required_proof'], 'rollback': proposal.get('rollback'),
            'context_blockers': context['blockers'], 'execution_authority': False, 'implementation_work': [],
            'source': context['source'], 'base_revision': context['base_revision']}
