"""Lifecycle commands for the SAM backend.

Wraps the AWS SAM CLI for build, validate, deploy, delete plus local
development (sam local invoke, sam local start-api, sam logs).

All commands run with cwd=`serverless/` (the repo root has a separate
purpose; the SAM template lives in the module folder).
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Any

from shared.console import CYAN
from shared.console import GREEN
from shared.console import NC
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


# Path al modulo serverless/ desde el root del repo.
_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'


def _ensure_sam_available() -> None:
    """Verifica que `sam` esta en el PATH; aborta con hint si falta."""
    if shutil.which('sam') is None:
        _err('AWS SAM CLI no esta instalado')
        print(
            f'{YELLOW}  Instalar con:{NC} '
            f'{CYAN}brew install aws-sam-cli{NC} '
            f'o {CYAN}pip install aws-sam-cli{NC}',
        )
        print(
            f'{YELLOW}  Docs:{NC} '
            f'https://docs.aws.amazon.com/serverless-application-model/latest/'
            f'developerguide/install-sam-cli.html'
        )
        raise SystemExit(1)


def _ensure_serverless_dir() -> None:
    """Verifica que serverless/template.yaml existe."""
    template = _SERVERLESS_DIR / 'template.yaml'
    if not template.exists():
        _err(f'No se encuentra {template}')
        print(
            f'{YELLOW}  Primero crea el SAM template '
            f'(ver serverless/ARCHITECTURE.md){NC}'
        )
        raise SystemExit(1)


def _run_sam(args: list[str], *, check: bool = True) -> int:
    """Ejecuta `sam <args>` con cwd=serverless/, retorna exit code."""
    _ensure_sam_available()
    cmd = ['sam', *args]
    print(_c(CYAN, f'$ cd serverless/ && {" ".join(cmd)}'))
    result = subprocess.run(cmd, cwd=_SERVERLESS_DIR, check=False)
    if check and result.returncode != 0:
        _err(f'sam {args[0]} fallo con exit code {result.returncode}')
    return result.returncode


# ---------------------------------------------------------------------------
# Setup / Init
# ---------------------------------------------------------------------------


def cmd_init(flags: dict[str, Any]) -> int:
    """Setup inicial: verifica deps (sam, aws CLI) y uv sync del modulo."""
    _ensure_sam_available()

    if shutil.which('aws') is None:
        _err('AWS CLI no esta instalado')
        print(
            f'{YELLOW}  Instalar con:{NC} '
            f'{CYAN}brew install awscli{NC} o '
            f'{CYAN}pip install awscli{NC}'
        )
        return 1

    # uv sync del pyproject del modulo (si existe)
    pyproject = _SERVERLESS_DIR / 'pyproject.toml'
    if pyproject.exists():
        print(_c(CYAN, '$ uv sync --project serverless'))
        result = subprocess.run(
            ['uv', 'sync', '--project', str(_SERVERLESS_DIR)],
            check=False,
        )
        if result.returncode != 0:
            _err('uv sync fallo')
            return 1
    else:
        print(
            f'{YELLOW}  serverless/pyproject.toml no existe todavia. '
            f'Sera creado al implementar el modulo.{NC}'
        )

    print()
    print(_c(GREEN, 'OK  serverless/ listo para usar'))
    print(f'{YELLOW}Siguiente paso:{NC}')
    print('  python devtools/run.py serverless validate')
    print('  python devtools/run.py serverless build')
    return 0


# ---------------------------------------------------------------------------
# Build / Validate / Deploy
# ---------------------------------------------------------------------------


def cmd_validate(flags: dict[str, Any]) -> int:
    """sam validate template.yaml."""
    _ensure_serverless_dir()
    return _run_sam(['validate', '--lint'])


def cmd_build(flags: dict[str, Any]) -> int:
    """sam build --use-container (arm64 cross-platform Linux)."""
    _ensure_serverless_dir()
    args = ['build', '--use-container']
    if flags.get('no_cache'):
        args.append('--no-cached')
    if flags.get('function'):
        args.append(flags['function'])
    return _run_sam(args)


def cmd_deploy(flags: dict[str, Any]) -> int:
    """sam deploy --config-env <stage> (con --guided si no existe)."""
    _ensure_serverless_dir()
    stage = flags['stage']

    if stage == 'local':
        _err('Stage `local` no se deploya — usa `start-api` o `invoke`')
        return 1

    args = ['deploy', '--config-env', stage]
    if flags.get('guided'):
        args.append('--guided')

    overrides = flags.get('parameter_overrides')
    if overrides:
        args.extend(['--parameter-overrides', overrides])

    print(_c(YELLOW, f'Deploy a stage {stage}...'))
    return _run_sam(args)


def cmd_delete(flags: dict[str, Any]) -> int:
    """sam delete (destructivo, requiere --confirm o --dry-run)."""
    _ensure_serverless_dir()
    stage = flags['stage']

    if stage == 'local':
        _err('Stage `local` no tiene stack que eliminar')
        return 1

    if flags.get('dry_run'):
        print(_c(YELLOW, f'[dry-run] sam delete --config-env {stage}'))
        return 0

    args = ['delete', '--config-env', stage, '--no-prompts']
    return _run_sam(args)


# ---------------------------------------------------------------------------
# Local development
# ---------------------------------------------------------------------------


def cmd_invoke(flags: dict[str, Any]) -> int:
    """sam local invoke <Function> --event events/<X>.json."""
    _ensure_serverless_dir()

    function = flags.get('function')
    if not function:
        _err('--function es requerido (ej. --function=contact-form)')
        return 2

    # Convertir kebab-case (CLI) a PascalCase (LogicalId SAM)
    logical_id = (
        ''.join(part.capitalize() for part in function.split('-')) + 'Function'
    )

    args = ['local', 'invoke', logical_id]

    event = flags.get('event')
    if event:
        event_path = _SERVERLESS_DIR / event
        if not event_path.exists():
            _err(f'Event JSON no existe: {event_path}')
            return 1
        args.extend(['--event', event])

    if flags.get('debug'):
        args.append('--debug')

    return _run_sam(args)


def cmd_start_api(flags: dict[str, Any]) -> int:
    """sam local start-api (servidor HTTP local)."""
    _ensure_serverless_dir()
    args = ['local', 'start-api', '--port', str(flags.get('port', 3000))]
    if flags.get('debug'):
        args.append('--debug')

    print(_c(GREEN, f'API local en http://localhost:{flags.get("port", 3000)}'))
    print(_c(YELLOW, 'Ctrl+C para detener'))
    return _run_sam(args, check=False)


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


def cmd_logs(flags: dict[str, Any]) -> int:
    """sam logs -n <function> (ventana o --tail real-time)."""
    _ensure_serverless_dir()

    function = flags.get('function')
    if not function:
        _err('--function es requerido')
        return 2

    logical_id = (
        ''.join(part.capitalize() for part in function.split('-')) + 'Function'
    )

    args = ['logs', '-n', logical_id]

    if flags.get('tail') or flags.get('follow'):
        args.append('--tail')

    since = flags.get('since', '10m')
    args.extend(['-s', since])

    filter_pattern = flags.get('filter')
    if filter_pattern:
        args.extend(['--filter', filter_pattern])

    return _run_sam(args, check=False)


def cmd_tail(flags: dict[str, Any]) -> int:
    """Alias verbose de `logs --follow` con default function."""
    flags['tail'] = True
    return cmd_logs(flags)


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------


def cmd_clean(flags: dict[str, Any]) -> int:
    """Eliminar .aws-sam/ + __pycache__ + .pytest_cache."""
    targets = [
        _SERVERLESS_DIR / '.aws-sam',
        _SERVERLESS_DIR / '.pytest_cache',
        _SERVERLESS_DIR / '.ruff_cache',
        _SERVERLESS_DIR / '.coverage',
        _SERVERLESS_DIR / 'htmlcov',
    ]

    # __pycache__ recursivo
    pycache_dirs = list(_SERVERLESS_DIR.rglob('__pycache__'))
    targets.extend(pycache_dirs)

    if flags.get('dry_run'):
        for t in targets:
            if t.exists():
                print(_c(YELLOW, f'[dry-run] rm -rf {t}'))
        return 0

    for t in targets:
        if t.exists():
            print(_c(CYAN, f'rm -rf {t}'))
            if t.is_dir():
                shutil.rmtree(t)
            else:
                t.unlink()

    print(_c(GREEN, 'OK  caches limpios'))
    return 0


def cmd_smoke(flags: dict[str, Any]) -> int:
    """scripts/smoke_test.sh (curl contra endpoint deployed)."""
    _ensure_serverless_dir()
    stage = flags.get('stage', 'dev')
    script = _SERVERLESS_DIR / 'scripts' / 'smoke_test.sh'

    if not script.exists():
        _err(f'Smoke test no existe: {script}')
        print(
            f'{YELLOW}  Se creara al implementar el modulo. '
            f'Ver serverless/ARCHITECTURE.md{NC}'
        )
        return 1

    print(_c(CYAN, f'$ bash {script} {stage}'))
    result = subprocess.run(['bash', str(script), stage], check=False)
    return result.returncode
