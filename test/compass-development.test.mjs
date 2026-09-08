import { execFileSync } from 'node:child_process';
import test from 'node:test';

test('Compass development acceptance scenarios', () => {
  execFileSync('python3', ['skills/project-compass/scripts/test_compass_development.py'], { stdio: 'pipe' });
});

test('Compass distribution installs the canonical producer and behavior fixtures', () => {
  execFileSync('python3', ['scripts/verify_compass_distribution.py'], { stdio: 'pipe' });
});

test('Repository Python contracts match the hosted validation suite', () => {
  execFileSync('python3', ['-m', 'unittest', 'discover', '-s', 'tests'], { stdio: 'pipe', timeout: 120_000 });
});
