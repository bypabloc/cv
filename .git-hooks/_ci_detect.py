#!/usr/bin/env python3
"""CI helper: detect changed areas and emit GitHub Actions outputs.

Used by .github/workflows/ci.yml to decide whether to install Node, Docker,
etc. Emits to $GITHUB_OUTPUT:
    needs_docker=true|false
    needs_node=true|false
    has_work=true|false

Run via: uv run --project devtools python .git-hooks/_ci_detect.py
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _changed_files() -> list[str]:
    """Files changed vs base branch (or HEAD~1 fallback)."""
    base = os.environ.get('GITHUB_BASE_REF', '')
    if base:
        diff_base = f'origin/{base}'
        subprocess.run(
            ['git', 'fetch', 'origin', base, '--depth=1'],
            check=False, capture_output=True,
        )
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'{diff_base}...HEAD'],
            capture_output=True, text=True, check=False,
            cwd=str(PROJECT_ROOT),
        )
    else:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1...HEAD'],
            capture_output=True, text=True, check=False,
            cwd=str(PROJECT_ROOT),
        )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.splitlines() if f]


def _emit(key: str, value: str) -> None:
    """Append to $GITHUB_OUTPUT if available, else print."""
    out_path = os.environ.get('GITHUB_OUTPUT')
    line = f'{key}={value}'
    if out_path:
        with open(out_path, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')
    print(line)


def main() -> int:
    files = _changed_files()
    relevant = [
        f for f in files
        if f.startswith(('apps/', 'packages/', 'docker/', 'devtools/'))
        or f in ('package.json', 'pnpm-workspace.yaml', 'biome.json',
                 'tsconfig.json', 'tsconfig.base.json')
    ]
    has_work = bool(relevant)
    needs_docker = any(
        f.startswith(('docker/', 'devtools/docker/'))
        or f in ('docker-compose.yml',)
        for f in files
    ) or any(f.startswith('apps/') for f in files) or any(
        f.startswith('packages/') for f in files
    )
    needs_node = bool(relevant)

    _emit('has_work', 'true' if has_work else 'false')
    _emit('needs_docker', 'true' if needs_docker else 'false')
    _emit('needs_node', 'true' if needs_node else 'false')
    return 0


if __name__ == '__main__':
    sys.exit(main())
