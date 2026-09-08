"""Verify clean Compass installation, file parity, and installed behavior."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    manifest = json.loads((ROOT / 'catalog/manifest.json').read_text())
    asset = next(a for a in manifest['assets'] if a['id'] == 'project-compass')
    with tempfile.TemporaryDirectory(prefix='compass-install-check-') as directory:
        destination = Path(directory)
        subprocess.run([sys.executable, str(ROOT / 'scripts/workbench.py'), 'install', 'project-compass',
                        '--target', 'generic', '--root', str(destination), '--apply', '--json'],
                       check=True, capture_output=True, timeout=30)
        for name in asset['files']:
            if (ROOT / name).read_bytes() != (destination / name).read_bytes():
                raise ValueError('installed file differs: ' + name)
        for name in ('test_project_compass.py', 'test_compass_development.py'):
            subprocess.run([sys.executable, str(destination / 'skills/project-compass/scripts' / name)],
                           check=True, timeout=60)
        print(f"Installed {len(asset['files'])} manifest files with exact parity; legacy and development behavior passed.")


if __name__ == '__main__':
    main()
