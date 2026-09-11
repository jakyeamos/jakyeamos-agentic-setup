"""Behavioral regression cases for development preparation and evidence isolation."""
import json
import io
from contextlib import redirect_stdout
import os
from os import environ
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from compass_assessment import assess
from compass_change import change_context, prove
from compass_projection import family_projection
from test_project_compass import _contract, _registry, _scoped_contract, _continuity


def shared_fixture():
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(directory)
        folder = repo / '.project-compass/compasses'
        folder.mkdir(parents=True)
        now = '2026-09-08T12:00:00Z'
        registry = _registry(now)
        registry['compasses'][1]['status'] = 'draft'
        registry['links'][0]['status'] = 'unknown'
        registry['compasses'].append({'id': 'invalid', 'kind': 'subsystem', 'parent_id': 'project',
                                      'status': 'draft', 'path': 'compasses/invalid.json'})
        for relative, data in [('contract.json', _contract()), ('compasses.json', registry),
                               ('compasses/playback.json', _scoped_contract('playback', 'project', ['usable-loop']))]:
            data['updated_at'] = now
            (repo / '.project-compass' / relative).write_text(json.dumps(data, sort_keys=True) + '\n')
        (folder / 'invalid.json').write_text('{}\n')
        result = family_projection(repo)
        result['source'] = {'workspace': '/fixture', 'head': None, 'repository': None}
        result['generated_at'] = now
        return result


class DevelopmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        self.write('.project-compass/contract.json', _contract())
        registry = _registry('2026-09-08T12:00:00Z')
        registry['links'] = []
        self.write('.project-compass/compasses.json', registry)
        self.write('.project-compass/compasses/playback.json', _scoped_contract('playback', 'project', ['usable-loop']))
        self.write('src/playback.py', 'initial')
        self.write('src/unrelated.py', 'initial')
        self.write('spec.md', 'Preserve behavior')
        self.development = {'schema': 'compass-development/v1', 'revision': 1,
                            'inventory': {'source': 'git-tracked', 'include': ['src/*'], 'exclude': []},
                            'decisions': [{'id': 'fixture', 'status': 'accepted', 'source': 'conversation:fixture',
                                           'summary': 'Preserve the fixture behavior'}], 'bindings': []}
        for name, paths in [('project', []), ('playback', ['src/playback.py'])]:
            self.development['bindings'].append({'id': name, 'compass_id': name, 'authority': 'accepted',
                'decision_id': 'fixture', 'paths': paths, 'outcomes': ['usable-loop'], 'references': ['spec.md'],
                'proof': [{'id': name, 'command': [sys.executable, '-c', 'print("verified")'], 'oracle_ref': 'spec.md', 'receipt': '.project-compass/evidence/' + name + '.json'}]})
        self.save_development()
        self.run_git('init', '-q')
        self.run_git('add', '.')
        self.run_git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'baseline')

    def write(self, name, value):
        p = self.repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value) if not isinstance(value, str) else value)

    def run_git(self, *args):
        subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True,
                       env={**environ, 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'})

    def save_development(self):
        self.write('.project-compass/development.json', self.development)

    def context(self, **kwargs):
        return change_context(self.repo, paths=['src/playback.py'], compass_ids=[], base='HEAD', **kwargs)

    def proof(self):
        for name in ['project', 'playback']:
            prove(self.repo, name, name, [sys.executable, '-c', 'print("verified")'])

    def test_large_binary_dependency_is_hashed_and_invalidates_only_its_proof(self):
        import hashlib
        from compass_sources import MAX_BYTES, file_digest
        asset = self.repo / 'src/media.bin'
        payload = b'\x00\xff' * (MAX_BYTES // 2 + 1)
        asset.write_bytes(payload)
        self.development['bindings'][1]['dependencies'] = ['src/media.bin']
        self.save_development()
        self.assertEqual(file_digest(self.repo, 'src/media.bin'), hashlib.sha256(payload).hexdigest())
        self.proof()
        self.assertTrue(all(p['status'] == 'current' for p in self.context()['required_proof']))
        asset.write_bytes(payload[:-1] + b'\x01')
        statuses = {p['binding']: p['status'] for p in self.context()['required_proof']}
        self.assertEqual(statuses, {'project': 'current', 'playback': 'stale'})

    def test_digest_limit_is_inclusive_and_oversized_source_stays_invalid(self):
        from compass_sources import file_digest, reference
        asset = self.repo / 'src/media.bin'
        with patch('compass_sources.MAX_DIGEST_BYTES', 8):
            asset.write_bytes(b'12345678')
            self.assertIsNotNone(file_digest(self.repo, 'src/media.bin'))
            asset.write_bytes(b'123456789')
            with self.assertRaisesRegex(ValueError, 'digest source exceeds 8 bytes'):
                file_digest(self.repo, 'src/media.bin')
            self.assertEqual(reference(self.repo, 'src/media.bin')['status'], 'invalid')

    def test_digest_stream_checks_growth_and_uses_bounded_reads(self):
        from unittest.mock import MagicMock
        from compass_sources import DIGEST_CHUNK_BYTES, file_digest
        source = MagicMock()
        source.read.side_effect = [b'12345678', b'9', b'']
        with (patch('pathlib.Path.stat') as stat,
              patch('pathlib.Path.is_file', return_value=True),
              patch('pathlib.Path.open') as opened,
              patch('compass_sources.MAX_DIGEST_BYTES', 8)):
            stat.return_value.st_size = 8
            opened.return_value.__enter__.return_value = source
            with self.assertRaisesRegex(ValueError, 'digest source exceeds 8 bytes'):
                file_digest(self.repo, 'src/media.bin')
        self.assertTrue(all(call.args == (DIGEST_CHUNK_BYTES,) for call in source.read.call_args_list))

    def test_large_digest_does_not_relax_json_or_reference_boundaries(self):
        from compass_sources import MAX_BYTES, file_digest, read_json, reference
        self.write('large.json', '{"value": 1}' + ' ' * MAX_BYTES)
        self.assertIsNotNone(file_digest(self.repo, 'large.json'))
        with self.assertRaisesRegex(ValueError, 'source exceeds'):
            read_json(self.repo, 'large.json')
        self.assertEqual(reference(self.repo, 'large.json#/value')['status'], 'invalid')
        self.assertEqual(reference(self.repo, '../outside.bin')['status'], 'invalid')
        self.assertIsNone(file_digest(self.repo, 'missing.bin'))

    def test_legacy_root_readable_without_accepting_intent(self):
        (self.repo / '.project-compass/compasses.json').unlink()
        (self.repo / '.project-compass/development.json').unlink()
        family = family_projection(self.repo)
        self.assertEqual(family['root_summary']['status'], 'Ready')
        self.assertEqual(family['nodes'][0]['authority'], 'legacy-declared')
        self.assertEqual(family['coverage']['status'], 'unknown')

    def test_draft_and_invalid_child_remain_visible(self):
        registry = json.loads((self.repo / '.project-compass/compasses.json').read_text())
        registry['compasses'][1]['status'] = 'draft'
        self.write('.project-compass/compasses.json', registry)
        self.assertFalse(self.context()['eligible'])
        self.assertIn('src/playback.py', family_projection(self.repo)['coverage']['proposed_paths'])
        self.write('.project-compass/compasses/playback.json', '{')
        family = family_projection(self.repo)
        self.assertEqual(family['root_summary']['status'], 'Ready')
        self.assertFalse(family['nodes'][1]['valid'])
        self.assertEqual(family['status'], 'partial')

    def test_dangling_relationship_never_disappears(self):
        registry = json.loads((self.repo / '.project-compass/compasses.json').read_text())
        registry['links'] = [{'id': 'missing', 'from': 'playback', 'to': 'missing', 'kind': 'handoff',
                              'status': 'unknown', 'summary': 'Unknown consumer'}]
        self.write('.project-compass/compasses.json', registry)
        family = family_projection(self.repo)
        self.assertFalse(family['relationships'][0]['valid'])
        self.assertTrue(family['errors'])

    def test_shared_interface_includes_consumers(self):
        registry = json.loads((self.repo / '.project-compass/compasses.json').read_text())
        registry['compasses'].append({'id': 'consumer', 'kind': 'subsystem', 'path': 'compasses/consumer.json',
                                      'parent_id': 'project', 'status': 'draft'})
        registry['links'] = [{'id': 'shared', 'from': 'consumer', 'to': 'playback', 'kind': 'depends-on',
                              'status': 'aligned', 'summary': 'Consumes playback'}]
        self.write('.project-compass/compasses.json', registry)
        self.write('.project-compass/compasses/consumer.json', _scoped_contract('consumer', 'project', ['usable-loop']))
        self.assertIn('consumer', self.context()['affected_compasses'])

    def test_unrelated_edit_does_not_invalidate_proof(self):
        self.proof()
        self.write('src/unrelated.py', 'changed')
        self.assertTrue(all(p['status'] == 'current' for p in self.context()['required_proof']))
        self.write('spec.md', 'changed shared interface')
        self.assertTrue(all(p['status'] == 'stale' for p in self.context()['required_proof']))

    def test_actual_expansion_and_concurrent_intent_require_reassessment(self):
        prepared = self.context()
        self.write('src/unrelated.py', 'changed')
        complete = self.context(prepared=prepared, completion=True)
        self.assertIn('scope-expanded', {b['kind'] for b in complete['blockers']})
        contract = _contract()
        contract['revision'] = 2
        self.write('.project-compass/contract.json', contract)
        self.assertIn('intent-revision-changed', {b['kind'] for b in self.context(prepared=prepared)['blockers']})

    def test_rename_never_appears_covered(self):
        (self.repo / 'src/playback.py').rename(self.repo / 'src/renamed.py')
        coverage = family_projection(self.repo)['coverage']
        self.assertIn('src/renamed.py', coverage['unmapped_paths'])
        self.assertTrue(coverage['missing_paths'])
        self.assertIn('src/renamed.py', self.context(completion=True)['selected_paths'])

    def test_unrelated_invalid_child_does_not_block_bounded_completion(self):
        registry = json.loads((self.repo / '.project-compass/compasses.json').read_text())
        registry['compasses'].append({'id': 'legacy', 'kind': 'subsystem', 'path': 'compasses/legacy.json',
                                      'parent_id': 'project', 'status': 'draft'})
        self.write('.project-compass/compasses.json', registry)
        self.write('.project-compass/compasses/legacy.json', '{')
        self.run_git('add', '.')
        self.run_git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'legacy')
        prepared = self.context()
        self.write('src/playback.py', 'bounded change')
        self.proof()
        complete = self.context(prepared=prepared, completion=True)
        self.assertTrue(complete['eligible'], complete['blockers'])
        self.assertEqual(complete['unrelated_family_gaps'], 1)

    def test_unrelated_drafts_and_handoffs_are_counted_without_blocking(self):
        registry = json.loads((self.repo / '.project-compass/compasses.json').read_text())
        for name in ['legacy-a', 'legacy-b']:
            registry['compasses'].append({'id': name, 'kind': 'subsystem', 'path': 'compasses/' + name + '.json',
                                          'parent_id': 'project', 'status': 'draft'})
            self.write('.project-compass/compasses/' + name + '.json', _scoped_contract(name, 'project', ['usable-loop']))
        registry['links'] = [{'id': 'legacy-handoff', 'from': 'legacy-a', 'to': 'legacy-b',
                              'kind': 'handoff', 'status': 'unknown', 'summary': 'Unresolved legacy handoff'}]
        self.write('.project-compass/compasses.json', registry)
        result = self.context()
        self.assertTrue(result['eligible'], result['blockers'])
        self.assertEqual(result['unrelated_family_gaps'], 3)

    def test_inapplicable_modernization_creates_no_work(self):
        result = assess(self.repo, {'schema': 'compass-modernization-proposal/v1', 'paths': ['src/playback.py'],
                                   'applicable': False, 'trigger': 'model-release'})
        self.assertEqual(result['disposition'], 'not_applicable')
        self.assertFalse(result['execution_authority'])
        self.assertEqual(result['implementation_work'], [])

    def test_proof_rejects_sources_changed_by_command(self):
        command = [sys.executable, '-c', 'open("src/playback.py","w").write("mutated")']
        self.development['bindings'][1]['proof'][0]['command'] = command
        self.save_development()
        with self.assertRaisesRegex(ValueError, 'sources changed'):
            prove(self.repo, 'playback', 'playback', command)
        self.assertFalse((self.repo / '.project-compass/evidence/playback.json').exists())

    def test_completion_requires_original_packet(self):
        self.write('src/playback.py', 'changed')
        self.proof()
        self.assertIn('prepared-context-required', {b['kind'] for b in self.context(completion=True)['blockers']})

    def test_decision_revision_requires_reconciliation_and_new_proof(self):
        prepared = self.context()
        self.proof()
        self.development['decisions'][0]['summary'] = 'A changed acceptance decision'
        self.save_development()
        current = self.context(prepared=prepared)
        self.assertIn('intent-revision-changed', {b['kind'] for b in current['blockers']})
        self.assertTrue(all(p['status'] == 'stale' for p in current['required_proof']))

    def test_unreviewed_command_cannot_mint_proof(self):
        with self.assertRaisesRegex(ValueError, 'reviewed'):
            prove(self.repo, 'playback', 'playback', [sys.executable, '-c', 'pass'])

    def test_proposed_change_is_not_accepted(self):
        row = dict(self.development['bindings'][1], id='proposal', authority='proposed')
        self.development['bindings'].append(row)
        self.save_development()
        self.assertIn('intent-proposal-unreconciled', {b['kind'] for b in self.context()['blockers']})

    def test_shared_consumer_fixture_is_reproducible(self):
        expected = json.loads((Path(__file__).parents[1] / 'references/fixtures/family.json').read_text())
        self.assertEqual(shared_fixture(), expected)

    def test_pending_continuity_remains_a_blocker(self):
        self.write('.project-compass/continuity.json', _continuity())
        self.assertIn('continuity-conflict', {b['kind'] for b in self.context()['blockers']})

    def test_missing_behavior_reference_blocks_affected_scope(self):
        self.development['bindings'][1]['behavior_ids'] = ['missing']
        self.save_development()
        self.assertIn('missing-behavior-reference', {b['kind'] for b in self.context()['blockers']})

    def test_duplicate_proof_and_supersession_cycle_are_invalid(self):
        self.development['bindings'][1]['proof'] *= 2
        self.save_development()
        self.assertEqual(family_projection(self.repo)['development_status'], 'invalid')
        self.development['bindings'][1]['proof'] = self.development['bindings'][1]['proof'][:1]
        self.development['decisions'][0]['supersedes'] = 'fixture'
        self.save_development()
        self.assertEqual(family_projection(self.repo)['development_status'], 'invalid')

    def test_packet_carries_human_intent_and_decision_provenance(self):
        packet = self.context()
        self.assertTrue(packet['contracts'][0]['outcomes'][0]['intended'])
        self.assertEqual(packet['decisions'][0]['source'], 'conversation:fixture')

    def test_gate_checks_actual_diff_and_proof(self):
        packet = self.context()
        self.write('.quality-runner/compass/prepared.json', packet)
        self.write('.gitignore', '.quality-runner/\n')
        self.run_git('add', '.gitignore')
        self.run_git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'ignore')
        packet = self.context()
        self.write('.quality-runner/compass/prepared.json', packet)
        self.write('src/playback.py', 'changed')
        command = [sys.executable, str(Path(__file__).with_name('project_compass.py')), 'gate', str(self.repo), '--json']
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
        self.proof()
        result = subprocess.run(command, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.write('src/unrelated.py', 'expanded')
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)

    def test_cli_packet_serialization_preserves_obligations_and_limit(self):
        from compass_cli import main
        packet = self.context()
        packet['phase'] = 'completion'
        packet['eligible'] = True
        self.write('.quality-runner/compass/prepared.json', packet)
        for command in ('gate', 'change-context'):
            for size in ('small', 'compact', 'oversized'):
                with self.subTest(command=command, size=size):
                    result = json.loads(json.dumps(packet))
                    if size == 'compact':
                        result['constraints'] = [{'constraint': 'preserve'}] * 700
                    elif size == 'oversized':
                        result['constraints'] = ['preserve privacy \u2014 ' * 4000]
                    pretty = json.dumps(result, indent=2, sort_keys=True) + '\n'
                    compact = json.dumps(result, separators=(',', ':'), sort_keys=True) + '\n'
                    if size == 'compact':
                        self.assertGreater(len(pretty.encode()), 32768)
                        self.assertLessEqual(len(compact.encode()), 32768)
                    output = io.StringIO()
                    with patch('compass_change.change_context', return_value=result), redirect_stdout(output):
                        code = main([command, str(self.repo), '--json'])
                    self.assertLessEqual(len(output.getvalue().encode()), 32768)
                    if size == 'oversized' and command == 'gate':
                        self.assertEqual(code, 0)
                        self.assertEqual(json.loads(output.getvalue())['schema'], 'compass-gate-summary/v1')
                    elif size == 'oversized':
                        self.assertEqual(code, 2)
                        self.assertFalse(json.loads(output.getvalue())['eligible'])
                        self.assertEqual(json.loads(output.getvalue())['blockers'][0]['kind'], 'context-too-large')
                    else:
                        self.assertEqual(code, 0)
                        self.assertEqual(json.loads(output.getvalue()), result)
                        self.assertEqual(output.getvalue(), pretty if size == 'small' else compact)


if __name__ == '__main__':
    if sys.argv[1:] == ['--write-fixture']:
        (Path(__file__).parents[1] / 'references/fixtures/family.json').write_text(json.dumps(shared_fixture(), indent=2, sort_keys=True) + '\n')
    else:
        unittest.main()
