"""Hook orchestration for pre-commit and pre-push.

Consolidates all hook logic (file detection, classification, step execution)
in a single devtools script. The ``.git-hooks/pre-commit`` and
``.git-hooks/pre-push`` shell scripts are thin wrappers that just call:

    python devtools/run.py hooks --type=pre-commit
    python devtools/run.py hooks --type=pre-push

Behaviour:
    1. Detect changed files in server/, devtools/, dashboard/, landing/.
    2. If NONE of those modules has changes, exit 0 immediately (early-exit
       so a doc-only commit does not spin up Docker).
    3. Otherwise, run the registered steps for the hook type.

Steps live in ``.git-hooks/_common.py`` (STEP_REGISTRY) and rely on the
shared classification/coverage/purity helpers in ``devtools/shared/``.
"""

from pathlib import Path
import sys
from typing import Any


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _ensure_paths() -> None:
    """Add devtools/ and .git-hooks/ to sys.path."""
    devtools_path = str(_PROJECT_ROOT / 'devtools')
    if devtools_path not in sys.path:
        sys.path.insert(0, devtools_path)

    hooks_path = str(_PROJECT_ROOT / '.git-hooks')
    if hooks_path not in sys.path:
        sys.path.insert(0, hooks_path)


def _git_mode_for(hook_type: str) -> str:
    return 'staged' if hook_type == 'pre-commit' else 'unmerged'


def _detect_changed_files(git_mode: str) -> dict[str, list[str]]:
    """Run scan to find changed files for each module.

    Returns:
        dict with keys 'server', 'devtools', 'dashboard', 'landing' -> list of files.
    """
    from _common import get_frontend_files
    from _common import scan_files

    return {
        'server': scan_files(module='server', git_mode=git_mode),
        'devtools': scan_files(module='devtools', git_mode=git_mode),
        'dashboard': get_frontend_files('dashboard', git_mode),
        'landing': get_frontend_files('landing', git_mode),
    }


def _print_no_changes(hook_type: str) -> None:
    from _common import green
    from _common import out

    label = 'commit' if hook_type == 'pre-commit' else 'push'
    out('')
    out('=' * 80)
    out(
        green(
            f'  SIN CAMBIOS EN MÓDULOS RELEVANTES — {label.upper()} permitido'
        )
    )
    out(
        green(
            '  (server, dashboard, landing, devtools sin archivos modificados)'
        )
    )
    out('=' * 80)


def _build_classification(
    hook_type: str,
    server_files: list[str],
) -> dict:
    """Compute server source<->test classification for the hook."""
    from _common import classify_files
    from _common import scan_files

    git_mode = _git_mode_for(hook_type)
    coverage_source = scan_files(
        module='server',
        git_mode=git_mode,
        purpose='coverage',
    )
    coverage_source = [
        f
        for f in coverage_source
        if '/tests/' not in f and not f.startswith('devtools/')
    ]
    return classify_files(
        server_files,
        coverage_source,
        project_root=_PROJECT_ROOT,
    )


def _print_summary(
    hook_type: str,
    files: dict[str, list[str]],
    classification: dict,
) -> None:
    from _common import info
    from _common import out

    server_source = [f for f in files['server'] if '/tests/' not in f]
    if server_source:
        info(f'server/     : {len(server_source)} archivo(s) para conformance')
    if files['devtools']:
        info(
            f'devtools/   : {len(files["devtools"])} archivo(s) para conformance'
        )
    if classification['run_unit']:
        info(
            f'server/     : {len(classification["unit_pairs"])} par(es) source<->test'
        )
    if hook_type == 'pre-commit' and classification.get('run_integration'):
        info(
            'server/     : integration tests staged (NO se ejecutan en pre-commit)'
        )
    if files['dashboard']:
        info(f'dashboard/  : {len(files["dashboard"])} archivo(s) detectados')
    if files['landing']:
        info(f'landing/    : {len(files["landing"])} archivo(s) detectados')
    out('')


def _build_fail_fn(hook_type: str) -> Any:
    """Build the fail handler matching the hook type."""
    from _common import cyan
    from _common import fail
    from _common import out
    from _common import yellow

    blocked = (
        'COMMIT BLOQUEADO' if hook_type == 'pre-commit' else 'PUSH BLOQUEADO'
    )
    git_cmd = 'git commit' if hook_type == 'pre-commit' else 'git push'

    def show_skip() -> None:
        out('')
        out(yellow('Omitir TODAS las validaciones (emergencias):'))
        out(cyan(f'   {git_cmd} --no-verify'))
        out('')
        out(yellow('Omitir UN paso (no recomendado):'))
        for step in (
            'conformance',
            'dashboard_conformance',
            'landing_conformance',
            'frontend_purity',
            'mirror_enforcement',
            'deletion_mirror',
            'coverage',
            'dashboard_coverage',
            'landing_coverage',
            'integration',
            'dashboard_typecheck',
            'landing_typecheck',
        ):
            out(cyan(f'   SKIP_STEPS="{step}" {git_cmd} ...'))
        out('')

    def fail_fn(step_desc: str, extra_tip: str | None = None) -> int:
        return fail(step_desc, blocked, show_skip, extra_tip)

    return fail_fn


def _run_steps(
    hook_type: str,
    files: dict[str, list[str]],
    classification: dict,
    fail_fn: Any,
    deleted_by_module: dict[str, list[str]] | None = None,
) -> int:
    """Execute the registered steps for the hook type."""
    from _common import build_hook_context
    from _common import print_result_unified
    from _common import run_hook_steps

    config_file = _PROJECT_ROOT / '.git-hooks' / 'config.json'
    server_source = [f for f in files['server'] if '/tests/' not in f]

    context = build_hook_context(
        hook_name=hook_type,
        project_root=_PROJECT_ROOT,
        fail_fn=fail_fn,
        files_by_module={
            'server': server_source,
            'devtools': files['devtools'],
        },
        classification=classification,
        dashboard_files=files['dashboard'],
        landing_files=files['landing'],
        deleted_files_by_module=deleted_by_module,
    )

    result = run_hook_steps(
        hook_name=hook_type,
        config_file=config_file,
        context=context,
    )

    if isinstance(result, int):
        return result

    success_msg = (
        'TODAS LAS VALIDACIONES PASARON - Commit permitido'
        if hook_type == 'pre-commit'
        else 'TODAS LAS QUALITY GATES PASARON - Push permitido'
    )
    print_result_unified(result, context, success_msg=success_msg)
    return 0


def main(flags: dict[str, Any]) -> int:
    """Entry point invoked by ``devtools/run.py``."""
    _ensure_paths()

    hook_type = flags['type']

    from _common import header
    from _common import info

    title = (
        'PRE-COMMIT - Validaciones'
        if hook_type == 'pre-commit'
        else 'PRE-PUSH - Quality Gates'
    )
    header(title)

    if not (_PROJECT_ROOT / 'server' / 'manage.py').exists():
        from _common import err

        err('No se encontro server/manage.py')
        return 1

    git_mode = _git_mode_for(hook_type)
    info(f'Detectando archivos ({git_mode})...')

    files = _detect_changed_files(git_mode)

    deleted_by_module: dict[str, list[str]] = {
        'server': [],
        'dashboard': [],
        'landing': [],
    }
    if hook_type == 'pre-push':
        from _common import get_deleted_files_by_module

        deleted_by_module = get_deleted_files_by_module(_PROJECT_ROOT)
        if any(deleted_by_module.values()):
            total = sum(len(v) for v in deleted_by_module.values())
            info(f'eliminados   : {total} archivo(s) detectados (vs base)')

    has_any_changed = any(files.values())
    has_any_deleted = any(deleted_by_module.values())

    if not has_any_changed and not has_any_deleted:
        _print_no_changes(hook_type)
        return 0

    classification = _build_classification(hook_type, files['server'])

    has_work = (
        bool([f for f in files['server'] if '/tests/' not in f])
        or bool(files['devtools'])
        or classification['run_unit']
        or (hook_type == 'pre-push' and classification['run_integration'])
        or bool(files['dashboard'])
        or bool(files['landing'])
        or has_any_deleted
    )

    if not has_work:
        _print_no_changes(hook_type)
        return 0

    _print_summary(hook_type, files, classification)
    fail_fn = _build_fail_fn(hook_type)
    return _run_steps(
        hook_type,
        files,
        classification,
        fail_fn,
        deleted_by_module=deleted_by_module,
    )
