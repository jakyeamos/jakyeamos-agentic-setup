"""Artifact transport and oversized gate regressions through the public CLI."""
import hashlib
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from compass_cli import main
from compass_output import canonical_bytes
import test_compass_development as fixtures


class OutputTests(unittest.TestCase):
    setUp = fixtures.DevelopmentTests.setUp
    write = fixtures.DevelopmentTests.write
    run_git = fixtures.DevelopmentTests.run_git
    save_development = fixtures.DevelopmentTests.save_development
    context = fixtures.DevelopmentTests.context
    proof = fixtures.DevelopmentTests.proof

    def cli(self, *args, packet=None):
        output = io.StringIO()
        if packet is None:
            with redirect_stdout(output):
                code = main(list(args))
        else:
            with patch('compass_change.change_context', return_value=packet), redirect_stdout(output):
                code = main(list(args))
        return code, json.loads(output.getvalue()), len(output.getvalue().encode())

    def artifact(self, packet=None, path='.quality-runner/compass/entry.json'):
        return self.cli('change-context', str(self.repo), '--path', 'src/playback.py',
                        '--packet-output', str(path), '--json', packet=packet)

    def test_complete_artifact_and_normal_context_cap(self):
        packet = self.context()
        packet['preservation_payload'] = 'preserve' * 10000
        code, descriptor, size = self.artifact(packet)
        self.assertEqual(code, 0)
        self.assertEqual(descriptor['schema'], 'compass-packet-artifact/v1')
        data = Path(descriptor['artifact_path']).read_bytes()
        self.assertEqual(json.loads(data), packet)
        self.assertEqual(descriptor['artifact_digest'], hashlib.sha256(data).hexdigest())
        self.assertEqual(descriptor['artifact_bytes'], len(data))
        self.assertLess(size, 32768)
        self.assertEqual(self.cli('change-context', str(self.repo), '--json', packet=packet)[0], 2)
        # A descriptor is never an eligible prepared context.
        self.write('.quality-runner/compass/descriptor.json', descriptor)
        self.assertEqual(self.cli('gate', str(self.repo), '--prepared',
                                 '.quality-runner/compass/descriptor.json', '--json')[0], 1)

    def test_refuse_clobber_escape_and_symlink(self):
        self.artifact()
        target = self.repo / '.quality-runner/compass/entry.json'
        prior = target.read_bytes()
        self.assertEqual(self.artifact()[0], 1)
        self.assertEqual(target.read_bytes(), prior)
        for path in ['outside.json', '.quality-runner/compass/../escaped.json', self.repo.parent/'escaped.json']:
            with self.subTest(path=str(path)):
                self.assertEqual(self.artifact(path=path)[0], 1)
        (self.repo / '.quality-runner/compass/link').symlink_to(self.repo, target_is_directory=True)
        self.assertEqual(self.artifact(path='.quality-runner/compass/link/escape.json')[0], 1)
        self.assertFalse((self.repo/'escape.json').exists())

    def test_refuse_ineligible_completion_and_oversized_artifacts(self):
        for mutation in [{'eligible': False}, {'phase': 'completion'}, {'padding': 'x'*1048576}, {'affected_compasses': ['x'*40000]}]:
            packet = self.context()
            packet.update(mutation)
            self.assertEqual(self.artifact(packet)[0], 1)
            self.assertFalse((self.repo/'.quality-runner/compass/entry.json').exists())

    def test_large_gate_preserves_all_blockers_and_identity(self):
        entry = self.context()
        self.write('.quality-runner/compass/prepared.json', entry)
        for blockers in [[], [{'kind': k, 'action': 'reconcile'} for k in
                             ['stale-proof', 'scope-expansion', 'intent-revision',
                              'base-mismatch', 'workspace-mismatch', 'unresolved-intent']]]:
            packet = dict(entry, phase='completion', eligible=not blockers,
                          blockers=blockers, padding='x'*70000)
            code, result, size = self.cli('gate', str(self.repo), '--json', packet=packet)
            self.assertEqual(code, 2 if blockers else 0)
            self.assertEqual(result['schema'], 'compass-gate-summary/v1')
            self.assertEqual(result['blockers'], blockers)
            self.assertEqual(result['affected_compasses'], packet['affected_compasses'])
            self.assertEqual(result['full_result_digest'], hashlib.sha256(canonical_bytes(packet)).hexdigest())
            self.assertEqual(sum(result['proof_status_counts'].values()), len(packet['required_proof']))
            self.assertLessEqual(size, 32768)
        packet['blockers'] = [{'kind': 'unresolved-intent', 'action': 'x'*70000}]
        code, result, size = self.cli('gate', str(self.repo), '--json', packet=packet)
        self.assertEqual(code, 2)
        self.assertFalse(result['eligible'])
        self.assertEqual(result['blockers'][0]['kind'], 'context-too-large')
        self.assertLessEqual(size, 32768)

    def test_real_artifact_adoption_and_scope_expansion(self):
        code, descriptor, _ = self.artifact()
        self.assertEqual(code, 0)
        self.write('src/playback.py', 'changed')
        args = ['gate', str(self.repo), '--prepared', descriptor['artifact_path'], '--json']
        self.assertEqual(self.cli(*args)[0], 2)
        self.proof()
        self.assertEqual(self.cli(*args)[0], 0)
        self.write('src/unrelated.py', 'expanded')
        self.assertEqual(self.cli(*args)[0], 2)


if __name__ == '__main__':
    unittest.main()
