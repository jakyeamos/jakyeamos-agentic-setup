"""Review must establish a claim, not merely point at an existing file."""
import copy
import unittest

import test_compass_development as fixtures
from compass_assessment import assess, CLAIMS
from compass_sources import bindings, digest, reference
from compass_change import change_context


class AssessmentTests(unittest.TestCase):
    setUp = fixtures.DevelopmentTests.setUp
    write = fixtures.DevelopmentTests.write
    run_git = fixtures.DevelopmentTests.run_git
    save_development = fixtures.DevelopmentTests.save_development

    def proposal(self, kind='simplify'):
        self.write('review.md', 'Review: preserve explicit zero and consent boundaries; avoid duplicate work.')
        return {'schema': 'compass-modernization-proposal/v2', 'paths': ['src/playback.py'],
                'base_revision': self.head(), 'problem': 'Duplicate decoding adds work without changing outcomes',
                'expected_benefit': 'One decode per event with preserved behavior', 'applicable': True,
                'applicability_reason': 'The call trace repeats the same decode', 'evidence_refs': ['spec.md'],
                'rollback': 'Restore the previous implementation', 'remediation_id': 'existing-review-1',
                'reconsider_when': 'New consumers require independent decoding',
                'benefit_check': {'measures': ['decode-count'], 'baseline_ref': 'spec.md',
                                 'method': 'Compare the same workload', 'success_condition': 'One decode per event'},
                'selected_alternative': kind,
                'alternatives': [{'id': k, 'kind': k, 'summary': k + ' the decoding mechanism',
                                  'consequences': 'Preserve parsed result; deletion requires replacement',
                                  'consumer_impact': 'Playback callers keep the same result',
                                  'tradeoffs': 'Less repeated work versus migration effort',
                                  'outcome_ids': ['usable-loop'], 'evidence_refs': ['spec.md']}
                                 for k in ('delete', 'simplify', 'retain')]}

    def head(self):
        from compass_sources import git
        return git(self.repo, 'rev-parse', 'HEAD').strip()

    def review(self, subject, claims=CLAIMS, verdict='justified'):
        return {'schema': 'compass-assessment-review/v1', 'subject_digest': subject,
                'reviewer': 'fixture-reviewer', 'source_ref': 'review.md',
                'source_digest': reference(self.repo, 'review.md')['digest'],
                'verdict': verdict, 'rationale': 'Trace and specification support the selected alternative',
                'claims': {k: {'finding': 'supported', 'rationale': 'Compared claim with trace and specification',
                               'evidence': [reference(self.repo, 'spec.md')]} for k in claims}}

    def reviewed(self, kind='simplify'):
        proposal = self.proposal(kind)
        proposal['review'] = self.review(assess(self.repo, proposal)['review_target'],
                                         verdict='retain' if kind == 'retain' else 'justified')
        return proposal

    def test_existing_evidence_is_not_a_justified_recommendation(self):
        result = assess(self.repo, self.proposal())
        self.assertTrue(result['proposal_complete'])
        self.assertEqual(result['disposition'], 'insufficient_evidence')
        self.assertEqual(result['review']['status'], 'missing')

    def test_supported_simplification_is_advisory_only(self):
        result = assess(self.repo, self.reviewed())
        self.assertEqual(result['disposition'], 'worthwhile_now')
        self.assertFalse(result['execution_authority'])
        self.assertEqual(result['implementation_work'], [])

    def test_retain_requires_no_remediation_ticket(self):
        p = self.proposal('retain')
        del p['remediation_id']
        p['review'] = self.review(assess(self.repo, p)['review_target'], verdict='retain')
        self.assertEqual(assess(self.repo, p)['disposition'], 'retain_current_design')

    def test_contradicted_claim_cannot_pass_positive_review(self):
        p = self.reviewed()
        p['review']['claims']['preservation']['finding'] = 'contradicted'
        self.assertEqual(assess(self.repo, p)['disposition'], 'insufficient_evidence')
        p['review']['verdict'] = 'rejected'
        self.assertEqual(assess(self.repo, p)['disposition'], 'rejected')

    def test_changed_implementation_or_evidence_invalidates_review(self):
        p = self.reviewed()
        self.write('src/playback.py', 'changed implementation')
        self.assertEqual(assess(self.repo, p)['review']['status'], 'stale')
        p['review'] = self.review(assess(self.repo, p)['review_target'])
        self.write('spec.md', 'changed proof')
        self.assertEqual(assess(self.repo, p)['review']['status'], 'stale')

    def test_unrelated_edit_does_not_invalidate_review(self):
        p = self.reviewed()
        self.write('src/unrelated.py', 'independent edit')
        self.assertEqual(assess(self.repo, p)['disposition'], 'worthwhile_now')
        self.run_git('add', 'src/unrelated.py')
        self.run_git('commit', '-m', 'Unrelated change')
        self.assertEqual(assess(self.repo, p)['disposition'], 'worthwhile_now')

    def test_changing_choice_requires_review_again(self):
        p = self.reviewed()
        p['selected_alternative'] = 'delete'
        self.assertEqual(assess(self.repo, p)['review']['status'], 'stale')

    def test_legacy_never_silently_promotes_to_reviewed(self):
        p = self.proposal()
        p['schema'] = 'compass-modernization-proposal/v1'
        self.assertEqual(assess(self.repo, p)['disposition'], 'insufficient_evidence')
        p['applicable'] = False
        self.assertEqual(assess(self.repo, p)['disposition'], 'not_applicable')

    def test_missing_retain_and_unknown_outcomes_are_incomplete(self):
        p = self.proposal()
        p['alternatives'][-1]['kind'] = 'optimize'
        p['alternatives'][0]['outcome_ids'] = ['unknown-outcome']
        self.assertFalse(assess(self.repo, p)['proposal_complete'])

    def test_decision_assumptions_are_explicit_and_revision_bound(self):
        self.development['decisions'][0]['reasoning'] = {
            'schema': 'compass-decision-reasoning/v1', 'kind': 'implementation',
            'assumptions': [{'id': 'cost', 'statement': 'Decoding is expensive', 'status': 'supported',
                             'evidence_refs': ['spec.md'], 'reconsider_when': 'Decoder cost becomes negligible'}]}
        self.save_development()
        packet = change_context(self.repo, paths=['src/playback.py'], compass_ids=[], base=self.head())
        self.assertEqual(packet['decisions'][0]['reasoning']['kind'], 'implementation')
        self.development['decisions'][0]['reasoning']['assumptions'][0]['reconsider_when'] = ''
        self.save_development()
        with self.assertRaises(ValueError):
            bindings(self.repo)

    def test_benefit_requires_separate_observation_review(self):
        p = self.reviewed()
        prior = assess(self.repo, p)
        self.write('prior.json', prior)
        self.write('result.md', 'decode-count: before 2, after 1')
        p['observation'] = {'schema': 'compass-benefit-observation/v1', 'assessment_ref': 'prior.json',
                            'assessment_digest': digest(prior), 'result': 'realized',
                            'comparisons': [{'measure': 'decode-count', 'before': '2', 'after': '1',
                                             'interpretation': 'Reduced duplicate work', 'evidence_refs': ['result.md']}]}
        result = assess(self.repo, p)['benefit_observation']
        self.assertEqual(result['benefit_realized'], 'unknown')
        p['observation']['review'] = self.review(result['review_target'], ('attribution', 'measurement', 'preservation'))
        self.assertEqual(assess(self.repo, p)['benefit_observation']['benefit_realized'], 'realized')
        self.write('result.md', 'decode-count: before 2, after 2')
        self.assertEqual(assess(self.repo, p)['benefit_observation']['benefit_realized'], 'unknown')

    def test_planned_work_requires_current_plan_evidence(self):
        p = self.proposal()
        p['planned_work_ref'] = 'plan.md'
        self.assertFalse(assess(self.repo, p)['proposal_complete'])
        self.write('plan.md', 'Approved decoder replacement task')
        p['review'] = self.review(assess(self.repo, p)['review_target'])
        self.assertEqual(assess(self.repo, p)['disposition'], 'alongside_planned_work')
        self.write('plan.md', 'Replacement task cancelled')
        self.assertEqual(assess(self.repo, p)['review']['status'], 'stale')
        (self.repo / 'plan.md').unlink()
        self.assertFalse(assess(self.repo, p)['proposal_complete'])

    def test_malformed_alternative_is_incomplete(self):
        p = self.proposal()
        p['alternatives'][0]['kind'] = []
        p['selected_alternative'] = []
        self.assertFalse(assess(self.repo, p)['proposal_complete'])

    def test_assumption_evidence_selects_its_owner(self):
        self.write('assumption.md', 'Decoder cost evidence')
        self.development['decisions'][0]['reasoning'] = {
            'schema': 'compass-decision-reasoning/v1', 'kind': 'implementation',
            'assumptions': [{'id': 'cost', 'statement': 'Decoding costs matter', 'status': 'supported',
                            'evidence_refs': ['assumption.md'], 'reconsider_when': 'Cost changes'}]}
        self.save_development()
        packet = change_context(self.repo, paths=['assumption.md'], compass_ids=[], base=self.head())
        self.assertTrue(packet['bindings'])
        self.assertFalse(any(b['kind'] == 'unmapped-path' for b in packet['blockers']))

    def test_observation_cannot_swap_expected_benefit(self):
        p = self.reviewed()
        prior = assess(self.repo, p)
        self.write('prior.json', {**prior, 'expected_benefit': 'Invented promise'})
        p['observation'] = {'schema': 'compass-benefit-observation/v1', 'assessment_ref': 'prior.json',
                            'assessment_digest': digest(prior)}
        self.assertEqual(assess(self.repo, p)['benefit_observation']['status'], 'invalid')


if __name__ == '__main__':
    unittest.main()
