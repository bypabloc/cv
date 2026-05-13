"""Subprocess wrappers around the ``scan`` script for git-mode dispatch.

These shell out to ``python devtools/run.py scan ...`` and return the
``--only-list`` semicolon-separated output as a Python list. Kept apart
from ``git_mode.py`` so its execution logic does not have to import
``subprocess``/``sys`` machinery.
"""

from __future__ import annotations

import subprocess
import sys


def get_changed_files(*, module: str, git_mode: str) -> list[str]:
    """Get changed files for ``module`` using the scan script."""
    try:
        cmd = [
            sys.executable,
            'devtools/run.py',
            'scan',
            f'--git-mode={git_mode}',
            f'--module={module}',
            '--only-list',
            '--exclude-empty',
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        return [
            f.strip() for f in result.stdout.strip().split(';') if f.strip()
        ]
    except subprocess.SubprocessError, OSError:
        return []


def get_coverage_files(*, git_mode: str) -> list[str]:
    """Coverage-eligible server files via ``scan --purpose=coverage``."""
    try:
        cmd = [
            sys.executable,
            'devtools/run.py',
            'scan',
            f'--git-mode={git_mode}',
            '--module=server',
            '--purpose=coverage',
            '--only-list',
            '--exclude-empty',
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        files = [
            f.strip() for f in result.stdout.strip().split(';') if f.strip()
        ]
        return [f for f in files if '/tests/' not in f]
    except subprocess.SubprocessError, OSError:
        return []
