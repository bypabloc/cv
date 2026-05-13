"""Unified test runner entry point.

Orchestrates test execution across server (pytest), dashboard + landing (Vitest)
and e2e (Playwright). With ``--git-mode``: uses path mirroring + per-file
coverage. Without it: full suites. Optional ``--ui-review`` runs a Gemini
CLI pass over E2E screenshots after the suite finishes.

Heavy lifting lives in submodules so this file stays thin and the test
runner reads top-down:

    parse modules -> run (git or full) -> summarize -> evaluate -> ui_review
"""

from __future__ import annotations

import os
import sys
from typing import Any


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.compose import ensure_running
from shared.console import _header
from test_runner.full_suites import execute_full_suites
from test_runner.git_mode import execute_git_mode
from test_runner.modules import resolve_modules
from test_runner.summary import evaluate_results
from test_runner.summary import print_summary
from test_runner.ui_review import run_ui_review


def main(flags: dict[str, Any]) -> int:
    """Run tests across one or more modules."""
    env = flags['env']
    test_type = flags.get('type', 'all')
    git_mode = flags.get('git_mode')
    verbose = flags.get('verbose', False)
    quiet = flags.get('quiet', False)
    skip_empty = flags.get('skip_empty', True)
    screenshots = flags.get('screenshots', False)
    ui_review = flags.get('ui_review', False)
    project = flags.get('project', '') or ''
    shard = flags.get('shard')
    shard_total = flags.get('shard_total')
    fail_on_flaky = flags.get('fail_on_flaky', False)

    modules = resolve_modules(flags)

    if not modules:
        from shared.console import _warn

        _warn('No hay modulos que soporten ese tipo de test')
        return 0 if skip_empty else 1

    mode_label = f'git-mode={git_mode}' if git_mode else 'full'
    _header(f'test_runner [{test_type}] [{env}] [{mode_label}]')

    if verbose:
        print(f'  Modulos: {", ".join(modules)}')

    # Docker es necesario para server, dashboard, landing. Devtools corre en
    # el host (Python 3.14 via uv) y NO depende de Docker — saltar el
    # health check si solo testeamos devtools.
    needs_docker = bool(set(modules) - {'devtools'})
    if needs_docker and not ensure_running(env):
        return 1

    if git_mode:
        results = execute_git_mode(
            modules=modules,
            env=env,
            test_type=test_type,
            git_mode=git_mode,
            verbose=verbose,
            quiet=quiet,
            full_suite_runner=execute_full_suites,
        )
    else:
        results = execute_full_suites(
            modules=modules,
            env=env,
            test_type=test_type,
            verbose=verbose,
            quiet=quiet,
            screenshots=screenshots,
            project=project,
            shard=shard,
            shard_total=shard_total,
            fail_on_flaky=fail_on_flaky,
        )

    print_summary(results)
    rc = evaluate_results(results, skip_empty=skip_empty)

    if ui_review and rc == 0:
        review_rc = run_ui_review(verbose=verbose)
        if review_rc != 0:
            return review_rc

    return rc
