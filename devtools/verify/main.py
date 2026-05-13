"""verify main.

Dada una lista de archivos cambiados (staged/modified/all_changed):
1. Clasifica cada archivo por módulo y tipo (model, admin, service, view, etc.).
2. Determina las verificaciones aplicables según .claude/rules/verify-before-done.md.
3. Si --execute: corre cada verificación, captura exit + output truncado.
4. Reporta resultado humano (texto) o JSON estructurado (--json).

Exit codes:
- 0: todas las verificaciones pasaron (o sin --execute).
- 1: alguna verificación fallo (solo con --execute).
- 2: error de invocacion (sin archivos cambiados, etc).
"""

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
import json
import logging
from pathlib import Path
import re
import subprocess
from typing import Any

from shared.scan_helper import files_changed


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('verify')


@dataclass
class Verification:
    """Una verificación sugerida para un archivo."""

    reason: str
    cmd: str
    exit_code: int | None = None
    output: str = ''
    skipped: bool = False


@dataclass
class FileReport:
    """Reporte de un archivo cambiado y sus verificaciones."""

    file: str
    classification: str
    verifications: list[Verification] = field(default_factory=list)


def _resolve_git_mode(flags: dict[str, Any]) -> str:
    """Map verify flags to scan ``git_mode``.

    - ``--staged`` -> ``staged`` (git index)
    - ``--modified`` -> ``unstaged`` (working tree, sin staged)
    - default / ``--all-changed`` -> ``changed`` (staged+unstaged+untracked)
    """
    if flags.get('staged'):
        return 'staged'
    if flags.get('modified'):
        return 'unstaged'
    return 'changed'


def collect_changed_files(flags: dict[str, Any]) -> list[str]:
    """Return changed files based on flags (staged/modified/all_changed).

    Delegates to ``shared.scan_helper.files_changed``: la deteccion de
    archivos por estado git vive en ``devtools/scan/`` (fuente canonica).
    Así heredamos el filtrado de archivos eliminados, respeto a
    ``.gitignore``, y soporte para todos los modos git de scan.
    """
    git_mode = _resolve_git_mode(flags)
    return files_changed(git_mode=git_mode)


_SERVER_PATTERNS: list[tuple[str, str]] = [
    (r'apps/[^/]+/models(/|\.py$)', 'server_model'),
    (r'apps/[^/]+/admin(/|\.py$)', 'server_admin'),
    (r'apps/[^/]+/services/', 'server_service'),
    (r'apps/[^/]+/selectors/', 'server_selector'),
    (r'apps/[^/]+/views(/|\.py$)', 'server_view'),
    (r'apps/[^/]+/serializers(/|\.py$)', 'server_serializer'),
    (r'apps/[^/]+/tasks/', 'server_task'),
]


def _classify_server(path: str) -> str:
    """Classify a server/* path into a server_<type> category."""
    sub = path[len('server/') :]
    for pattern, label in _SERVER_PATTERNS:
        if re.match(pattern, sub):
            return label
    if path.endswith('.py'):
        return 'server_python'
    return 'server_other'


def _classify_dashboard(path: str) -> str:
    """Classify a dashboard/* path."""
    if path.endswith(('.ts', '.vue')):
        return 'dashboard_typescript'
    return 'dashboard_other'


def _classify_landing(path: str) -> str:
    """Classify a landing/* path."""
    if path.endswith(('.ts', '.astro')):
        return 'landing_typescript'
    return 'landing_other'


def _classify_devtools(path: str) -> str:
    """Classify a devtools/* path."""
    if path.endswith('.py'):
        return 'devtools_python'
    return 'devtools_other'


def _classify_claude(path: str) -> str:
    """Classify a .claude/* path."""
    if path.endswith('.json'):
        return 'claude_json'
    if path.endswith('.sh'):
        return 'claude_shell'
    return 'claude_other'


def classify_file(path: str) -> str:
    """Classify file path into a logical category for verification."""
    if re.search(r'(tests?/|/migrations/|__init__\.py$)', path):
        return 'test_or_migration_or_init'

    if path.startswith('server/'):
        return _classify_server(path)
    if path.startswith('dashboard/'):
        return _classify_dashboard(path)
    if path.startswith('landing/'):
        return _classify_landing(path)
    if path.startswith('devtools/'):
        return _classify_devtools(path)
    if path.startswith('.claude/'):
        return _classify_claude(path)

    return 'other'


def verifications_for(classification: str) -> list[Verification]:
    """Return list of verifications applicable to a given classification."""
    devtools_run = 'python devtools/run.py'

    mapping: dict[str, list[Verification]] = {
        'server_model': [
            Verification(
                reason='Modelo modificado: regenerar migrations',
                cmd=(
                    'docker exec portfolio-server-local '
                    'python manage.py makemigrations --dry-run'
                ),
            ),
            Verification(
                reason='Modelo modificado: lint Python',
                cmd=f'{devtools_run} docker lint',
            ),
            Verification(
                reason='Modelo modificado: unit tests del modelo',
                cmd=f'{devtools_run} test_runner --module=server --type=unit',
            ),
        ],
        'server_admin': [
            Verification(
                reason='Admin modificado: Django check',
                cmd=(
                    'docker exec portfolio-server-local python manage.py check'
                ),
            ),
            Verification(
                reason='Admin modificado: lint Python',
                cmd=f'{devtools_run} docker lint',
            ),
        ],
        'server_service': [
            Verification(
                reason='Service modificado: lint + unit tests',
                cmd=f'{devtools_run} docker lint',
            ),
            Verification(
                reason='Service modificado: unit tests',
                cmd=f'{devtools_run} test_runner --module=server --type=unit',
            ),
        ],
        'server_selector': [
            Verification(
                reason='Selector modificado: lint + unit tests',
                cmd=f'{devtools_run} docker lint',
            ),
            Verification(
                reason='Selector modificado: unit tests',
                cmd=f'{devtools_run} test_runner --module=server --type=unit',
            ),
        ],
        'server_view': [
            Verification(
                reason='View modificado: lint + integration tests',
                cmd=f'{devtools_run} docker lint',
            ),
            Verification(
                reason='View modificado: integration tests',
                cmd=(
                    f'{devtools_run} test_runner '
                    '--module=server --type=integration'
                ),
            ),
        ],
        'server_serializer': [
            Verification(
                reason='Serializer modificado: lint + unit tests',
                cmd=f'{devtools_run} docker lint',
            ),
            Verification(
                reason='Serializer modificado: unit tests',
                cmd=f'{devtools_run} test_runner --module=server --type=unit',
            ),
        ],
        'server_task': [
            Verification(
                reason='Task modificado: lint',
                cmd=f'{devtools_run} docker lint',
            ),
        ],
        'server_python': [
            Verification(
                reason='Python server modificado: lint',
                cmd=f'{devtools_run} docker lint',
            ),
        ],
        'dashboard_typescript': [
            Verification(
                reason='Dashboard TS/Vue modificado: typecheck',
                cmd=(
                    f'{devtools_run} test_runner --module=dashboard --type=typecheck'
                ),
            ),
            Verification(
                reason='Dashboard TS/Vue modificado: lint Biome',
                cmd=f'{devtools_run} docker lint --module=dashboard',
            ),
        ],
        'landing_typescript': [
            Verification(
                reason='Landing TS/Astro modificado: typecheck',
                cmd=(
                    f'{devtools_run} test_runner '
                    '--module=landing --type=typecheck'
                ),
            ),
            Verification(
                reason='Landing TS/Astro modificado: lint Biome',
                cmd=f'{devtools_run} docker lint --module=landing',
            ),
        ],
        'devtools_python': [
            Verification(
                reason='Devtools Python modificado: pytest via test_runner',
                cmd=f'{devtools_run} test_runner --module=devtools --type=unit',
            ),
        ],
        'claude_json': [
            Verification(
                reason='settings.json modificado: validar JSON',
                cmd='python3 -m json.tool .claude/settings.json',
            ),
        ],
        'claude_shell': [
            Verification(
                reason='Hook bash modificado: syntax check',
                cmd='bash -n .claude/hooks/*.sh',
            ),
        ],
    }

    # No-op classifications.
    skip_classes = {
        'test_or_migration_or_init',
        'server_other',
        'dashboard_other',
        'landing_other',
        'devtools_other',
        'claude_other',
        'other',
    }
    if classification in skip_classes:
        return []

    return mapping.get(classification, [])


def build_reports(files: list[str]) -> list[FileReport]:
    """Build verification reports for each file."""
    reports = []
    for f in files:
        classification = classify_file(f)
        verifications = verifications_for(classification)
        reports.append(
            FileReport(
                file=f,
                classification=classification,
                verifications=verifications,
            ),
        )
    return reports


def deduplicate_commands(reports: list[FileReport]) -> list[Verification]:
    """Deduplicate verifications by cmd: same cmd from multiple files runs once."""
    seen: dict[str, Verification] = {}
    for r in reports:
        for v in r.verifications:
            if v.cmd in seen:
                continue
            seen[v.cmd] = Verification(reason=v.reason, cmd=v.cmd)
    return list(seen.values())


def execute_verifications(verifications: list[Verification]) -> int:
    """Run each verification, populate exit_code/output. Return overall exit code."""
    overall = 0
    for v in verifications:
        try:
            result = subprocess.run(  # noqa: S602
                v.cmd,
                shell=True,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
            v.exit_code = result.returncode
            # Truncar output a 2000 chars para reporte legible.
            combined = (result.stdout + result.stderr).strip()
            v.output = combined[:2000] + (
                '\n... (truncado)' if len(combined) > 2000 else ''
            )
        except subprocess.TimeoutExpired:
            v.exit_code = -1
            v.output = '<TIMEOUT después de 120s>'
        except OSError as e:
            v.exit_code = -2
            v.output = f'<ERROR ejecutando: {e}>'

        if v.exit_code != 0:
            overall = 1

    return overall


def _render_files_by_classification(reports: list[FileReport]) -> None:
    """Print files grouped by classification."""
    by_classification: dict[str, list[str]] = {}
    for r in reports:
        by_classification.setdefault(r.classification, []).append(r.file)

    for classification, fs in sorted(by_classification.items()):
        logger.info('  [%s] %d archivo(s)', classification, len(fs))
        for f in fs[:5]:
            logger.info('    - %s', f)
        if len(fs) > 5:
            logger.info('    ... y %d mas', len(fs) - 5)


def _verification_marker(v: Verification, *, executed: bool) -> str:
    """Compute the [OK]/[FAIL]/[SKIPPED] marker for a verification."""
    if not executed:
        return ''
    if v.exit_code == 0:
        return ' [OK]'
    if v.exit_code is None:
        return ' [SKIPPED]'
    return f' [FAIL exit={v.exit_code}]'


def render_text(
    files: list[str],
    reports: list[FileReport],
    verifications: list[Verification],
    *,
    executed: bool,
) -> None:
    """Render human-readable output to stdout."""
    if not files:
        logger.info('verify: sin archivos cambiados.')
        return

    logger.info('verify: %d archivo(s) cambiado(s).', len(files))
    logger.info('')

    _render_files_by_classification(reports)

    if not verifications:
        logger.info('')
        logger.info('verify: ninguna verificación aplica para estos archivos.')
        return

    logger.info('')
    logger.info('Verificaciones sugeridas (%d únicas):', len(verifications))
    for v in verifications:
        marker = _verification_marker(v, executed=executed)
        logger.info('  - %s%s', v.reason, marker)
        logger.info('    %s', v.cmd)
        if executed and v.exit_code != 0 and v.output:
            logger.info(
                '    --- output ---\n%s\n    --------------',
                v.output,
            )


def render_json(
    files: list[str],
    reports: list[FileReport],
    verifications: list[Verification],
) -> None:
    """Render JSON output to stdout (parseable by ``jq`` / ``json.load``).

    Uses ``print`` directly (not ``logger.info``) because ``logging`` writes
    to stderr by default — that defeats ``verify --json | jq ...`` and any
    agent that pipes the output. Decorative text (``render_human``) keeps
    using ``logger.info`` since it lives on stderr alongside the bootstrap
    banners.
    """
    payload = {
        'files': files,
        'reports': [asdict(r) for r in reports],
        'verifications': [asdict(v) for v in verifications],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main(flags: dict[str, Any]) -> int:
    """Entry point for verify script."""
    files = collect_changed_files(flags)
    reports = build_reports(files)
    verifications = deduplicate_commands(reports)

    overall_exit = 0
    executed = bool(flags.get('execute'))
    if executed and verifications:
        overall_exit = execute_verifications(verifications)

    if flags.get('json'):
        render_json(files, reports, verifications)
    else:
        render_text(files, reports, verifications, executed=executed)

    if not files:
        return 0
    return overall_exit
