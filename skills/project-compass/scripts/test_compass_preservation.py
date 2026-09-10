"""Intent-preservation cases: green ordinary tests must not hide lost behavior."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from compass_change import change_context, prove
from compass_projection import family_projection
import test_compass_development as fixtures


class PreservationTests(unittest.TestCase):
    setUp = fixtures.DevelopmentTests.setUp
    write = fixtures.DevelopmentTests.write
    run_git = fixtures.DevelopmentTests.run_git
    save_development = fixtures.DevelopmentTests.save_development
    context = fixtures.DevelopmentTests.context

    def enroll(self):
        self.development['preservation'] = 'compass-preservation/v1'
        self.development['inventory']['behavior_ref'] = 'behaviors.json'
        self.write('behaviors.json', {'behaviors': [{'id': 'privacy', 'spec_ref': 'spec.md'}]})
        for row in self.development['bindings']:
            row.update(behavior_ids=['privacy'], constraints=['Records stay private until consent'],
                       handoff_review='No external handoff in this bounded fixture')
            row['proof'][0]['behavior_ids'] = ['privacy']
        self.save_development()

    def test_absent_inventory_is_unknown_and_enrolled_scope_blocks(self):
        family = family_projection(self.repo)
        self.assertEqual(family['coverage']['behavior_status'], 'unknown')
        self.assertTrue(self.context()['eligible'])  # Legacy contracts remain readable.
        self.development['preservation'] = 'compass-preservation/v1'
        self.save_development()
        self.assertFalse(self.context()['eligible'])

    def test_linked_bootstrap_requires_specs_and_behavior_specific_proof(self):
        self.enroll()
        self.assertTrue(self.context()['eligible'], self.context()['blockers'])
        self.development['bindings'][1]['proof'][0]['behavior_ids'] = []
        self.save_development()
        self.assertFalse(self.context()['eligible'])
        self.assertIn('behavior-proof-missing:privacy', family_projection(self.repo)['bootstrap']['subsystems'][1]['gaps'])

    def test_invalid_inventory_is_not_measured_zero(self):
        self.enroll()
        self.write('behaviors.json', {'behaviors': [{'id': 'privacy'}, {'id': 'privacy'}]})
        self.assertEqual(family_projection(self.repo)['coverage']['behavior_status'], 'invalid')
        self.assertFalse(self.context()['eligible'])

    def test_continuation_keeps_original_base_scope_and_intent(self):
        self.enroll()
        prepared = self.context()
        result = change_context(self.repo, paths=['src/unrelated.py'], compass_ids=[], base=prepared['base_revision'],
                                prepared=prepared, continuation=True)
        self.assertEqual(result['selected_paths'], ['src/playback.py', 'src/unrelated.py'])
        self.assertEqual(result['base_revision'], prepared['base_revision'])
        self.assertIn('playback', result['affected_compasses'])
        self.assertTrue(result['preservation']['parent_packet_digest'])
        self.development['bindings'][1]['constraints'] = ['All records public']
        self.save_development()
        changed = change_context(self.repo, paths=[], compass_ids=[], base=prepared['base_revision'],
                                 prepared=prepared, continuation=True)
        self.assertIn('intent-revision-changed', {b['kind'] for b in changed['blockers']})

    def test_behavior_spec_edit_invalidates_only_relevant_proof(self):
        self.enroll()
        for row in self.development['bindings']:
            prove(self.repo, row['id'], row['id'], row['proof'][0]['command'])
        self.write('behaviors.json', {'behaviors': [{'id': 'privacy', 'spec_ref': 'spec.md'}, {'id': 'other', 'spec_ref': 'other.md'}]})
        self.assertTrue(all(p['status'] == 'current' for p in self.context()['required_proof']))
        self.write('other.md', 'Different meaning')
        self.write('behaviors.json', {'behaviors': [{'id': 'privacy', 'spec_ref': 'other.md'}]})
        self.assertTrue(all(p['status'] == 'stale' for p in self.context()['required_proof']))

    def test_green_smoke_cannot_substitute_for_privacy_oracle(self):
        self.enroll()
        # Ordinary tests exercise admitted records only; optimization accidentally drops consent.
        source = 'def visible(record):\n    return record["consent"]\n'
        self.write('src/playback.py', source)
        self.write('oracle.py', 'from src.playback import visible\nassert visible({"consent": True})\nassert not visible({"consent": False})\n')
        row = self.development['bindings'][1]
        row['proof'][0].update(command=[sys.executable, 'oracle.py'], oracle_ref='oracle.py')
        self.save_development()
        self.assertEqual(prove(self.repo, 'playback', 'playback', row['proof'][0]['command'])['exit_code'], 0)
        prepared = self.context()
        self.write('src/playback.py', 'def visible(record):\n    return True\n')
        smoke = subprocess.run([sys.executable, '-c', 'from src.playback import visible; assert visible({"consent": True})'], cwd=self.repo)
        self.assertEqual(smoke.returncode, 0)
        self.assertNotEqual(prove(self.repo, 'playback', 'playback', row['proof'][0]['command'])['exit_code'], 0)
        complete = self.context(prepared=prepared, completion=True)
        self.assertTrue(any(b['kind'] == 'required-proof' and b.get('binding') == 'playback' for b in complete['blockers']))
        self.write('src/playback.py', source)
        self.assertEqual(prove(self.repo, 'playback', 'playback', row['proof'][0]['command'])['exit_code'], 0)

    def test_rating_zero_survives_a_cleaner_normalizer(self):
        self.enroll()
        self.write('src/playback.py', 'def rating(value):\n    return value if value is not None else 5\n')
        self.write('oracle.py', 'from src.playback import rating\nassert rating(0) == 0\nassert rating(None) == 5\n')
        row = self.development['bindings'][1]
        row['proof'][0].update(command=[sys.executable, 'oracle.py'], oracle_ref='oracle.py')
        self.save_development()
        self.assertEqual(prove(self.repo, 'playback', 'playback', row['proof'][0]['command'])['exit_code'], 0)
        self.write('src/playback.py', 'def rating(value):\n    return value or 5\n')
        smoke = subprocess.run([sys.executable, '-c', 'from src.playback import rating; assert rating(4) == 4'], cwd=self.repo)
        self.assertEqual(smoke.returncode, 0)
        self.assertEqual(prove(self.repo, 'playback', 'playback', row['proof'][0]['command'])['exit_code'], 1)

    def test_failed_continuation_cannot_normalize_changed_intent(self):
        self.enroll()
        prepared = self.context()
        self.development['bindings'][1]['constraints'] = ['Changed intent']
        self.save_development()
        first = self.context(prepared=prepared, continuation=True)
        second = self.context(prepared=first, continuation=True)
        self.assertFalse(first['eligible'])
        self.assertIn('prepared-context-ineligible', {b['kind'] for b in second['blockers']})

    def test_exclusion_does_not_hide_explicit_dependency(self):
        self.enroll()
        self.development['inventory']['exclude'] = [{'pattern': 'src/unrelated.py', 'kind': 'generated', 'reason': 'Generated input'}]
        self.development['bindings'][1]['dependencies'] = ['src/unrelated.py']
        self.save_development()
        packet = change_context(self.repo, paths=['src/unrelated.py'], compass_ids=[], base='HEAD')
        self.assertIn('playback', packet['direct_compasses'])
        self.assertIn('playback', {p['binding'] for p in packet['required_proof']})

    def test_missing_oracle_prevents_linked_bootstrap(self):
        self.enroll()
        self.development['bindings'][1]['proof'][0]['oracle_ref'] = 'absent.py'
        self.save_development()
        self.assertFalse(self.context()['eligible'])
        self.assertIn('proof-oracle-unavailable:playback', family_projection(self.repo)['bootstrap']['subsystems'][1]['gaps'])

    def test_inherited_root_does_not_block_unrelated_handoff(self):
        self.enroll()
        registry = json.loads((self.repo / '.project-compass/compasses.json').read_text())
        link = fixtures._registry('2026-09-08T12:00:00Z')['links'][0]
        registry['compasses'].append({'id': 'neighbor', 'kind': 'subsystem', 'parent_id': 'project', 'status': 'active', 'path': 'compasses/neighbor.json'})
        self.write('.project-compass/compasses/neighbor.json', fixtures._scoped_contract('neighbor', 'project', ['usable-loop']))
        link.update({'from': 'project', 'to': 'neighbor', 'status': 'unknown'})
        registry['links'] = [link]
        self.write('.project-compass/compasses.json', registry)
        packet = self.context()
        self.assertTrue(packet['eligible'], packet['blockers'])
        self.assertTrue(packet['unrelated_family_gaps'])
        self.assertIn('handoff-unresolved', family_projection(self.repo)['bootstrap']['subsystems'][0]['gaps'])

    def test_commitments_visible_revision_bound_and_scoped(self):
        self.enroll()
        continuity = fixtures._continuity()
        continuity['reconciliations'] = []
        self.write('.project-compass/continuity.json', continuity)
        prepared = self.context()
        self.assertEqual(prepared['commitments'][0]['statement'], 'Preserve the proven user loop.')
        row = self.development['bindings'][1]
        prove(self.repo, 'playback', 'playback', row['proof'][0]['command'])
        continuity['commitments'][0]['statement'] = 'Replace the original user loop.'
        self.write('.project-compass/continuity.json', continuity)
        self.assertEqual(self.context()['required_proof'][1]['status'], 'stale')
        changed = self.context(prepared=prepared, continuation=True)
        self.assertIn('intent-revision-changed', {b['kind'] for b in changed['blockers']})
        registry = json.loads((self.repo / '.project-compass/compasses.json').read_text())
        registry['compasses'].append({'id': 'neighbor', 'kind': 'subsystem', 'parent_id': 'project', 'status': 'active', 'path': 'compasses/neighbor.json'})
        self.write('.project-compass/compasses/neighbor.json', fixtures._scoped_contract('neighbor', 'project', ['usable-loop']))
        self.write('.project-compass/compasses.json', registry)
        continuity['commitments'][0].update(compass_ids=['neighbor'], status='unresolved')
        self.write('.project-compass/continuity.json', continuity)
        self.assertEqual(self.context()['commitments'], [])
        self.assertTrue(self.context()['eligible'])

    def test_unknown_or_removed_commitment_scope_blocks(self):
        self.enroll()
        continuity = fixtures._continuity()
        continuity['reconciliations'] = []
        for scope in ['playbak', 'removed-subsystem']:
            continuity['commitments'][0]['compass_ids'] = [scope]
            self.write('.project-compass/continuity.json', continuity)
            self.assertFalse(self.context()['eligible'])
            self.assertEqual(family_projection(self.repo)['continuity']['status'], 'invalid')

    def test_two_milestones_complete_against_original_base(self):
        self.enroll()
        self.development['bindings'][1]['paths'].append('src/unrelated.py')
        self.save_development()
        self.run_git('add', '.')
        self.run_git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'enrollment')
        prepared = self.context()
        self.write('src/playback.py', 'milestone one')
        self.run_git('add', 'src/playback.py')
        self.run_git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'first')
        next_packet = change_context(self.repo, paths=['src/unrelated.py'], compass_ids=[],
                                     base=prepared['base_revision'], prepared=prepared, continuation=True)
        self.assertTrue(next_packet['eligible'], next_packet['blockers'])
        self.write('src/unrelated.py', 'milestone two')
        for row in self.development['bindings']:
            prove(self.repo, row['id'], row['id'], row['proof'][0]['command'])
        result = change_context(self.repo, paths=[], compass_ids=[], base=prepared['base_revision'],
                                prepared=next_packet, completion=True)
        self.assertTrue(result['eligible'], result['blockers'])
        self.assertEqual(result['selected_paths'], ['src/playback.py', 'src/unrelated.py'])

    def test_summary_reports_counts_without_partial_coverage_arrays(self):
        from compass_projection import family_summary
        summary = family_summary(family_projection(self.repo))
        self.assertEqual(summary['schema'], 'compass-family-summary/v1')
        self.assertIsInstance(summary['coverage']['unmapped_paths'], int)
        self.assertTrue(summary['detail_omitted'])
        self.assertLess(len(json.dumps(summary)), 32768)


if __name__ == '__main__':
    unittest.main()
