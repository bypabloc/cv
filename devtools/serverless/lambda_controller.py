"""Comandos para lambdas que siguen el formato lambda-controller.

Estos comandos operan sobre cualquier lambda resuelto por `--path`
(directorio con `lambda.yaml`). Generan el SAM template efimero desde el
manifiesto y lo usan por detras para `sam local invoke`, `sam build` +
`sam deploy`, y `aws lambda invoke` contra un stage deployado.

Para el backend SAM del portfolio (modo legacy, sin `--path`) ver
`serverless/lifecycle.py` y `serverless/testing.py`.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from serverless.resolve import ManifestError
from serverless.resolve import ResolvedLambda
from serverless.resolve import resolve_lambda
from serverless.sam_generate import generate_sam_file
from shared.console import CYAN
from shared.console import GREEN
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


def _ensure_tool(tool: str, install_hint: str) -> None:
    """Verifica que `tool` esta en el PATH; aborta con hint si falta."""
    if shutil.which(tool) is None:
        _err(f'{tool} no esta instalado')
        print(_c(YELLOW, f'  {install_hint}'))
        raise SystemExit(1)


def _require_lambda_controller(flags: dict[str, Any]) -> ResolvedLambda:
    """Resuelve el lambda y exige que sea modo lambda-controller.

    Raises
    ------
    SystemExit
        Si no se paso `--path`/`--module` (modo legacy no aplica aqui).
    """
    resolved = resolve_lambda(flags)
    if not resolved.is_lambda_controller:
        _err(
            'Este comando requiere --path=<dir> de un lambda-controller '
            '(directorio con lambda.yaml).',
        )
        raise SystemExit(2)
    return resolved


def _regenerate_sam(resolved: ResolvedLambda, stage: str) -> Path:
    """Regenera el template.yaml efimero del lambda para un stage."""
    template = generate_sam_file(resolved, stage=stage)
    print(_c(CYAN, f'SAM generado: {template} (stage {stage})'))
    return template


def _run(cmd: list[str], *, cwd: Path) -> int:
    """Ejecuta un comando, imprime la invocacion, devuelve exit code."""
    print(_c(CYAN, f'$ cd {cwd} && {" ".join(cmd)}'))
    result = subprocess.run(cmd, cwd=cwd, check=False)
    return result.returncode


# ---------------------------------------------------------------------------
# sam-generate
# ---------------------------------------------------------------------------


def cmd_sam_generate(flags: dict[str, Any]) -> int:
    """Genera template.yaml desde lambda.yaml (sin build ni deploy)."""
    resolved = _require_lambda_controller(flags)
    stage = flags.get('stage', 'dev')
    try:
        _regenerate_sam(resolved, stage)
    except ManifestError as exc:
        _err(str(exc))
        return 1
    print(_c(GREEN, 'OK  template.yaml generado'))
    return 0


# ---------------------------------------------------------------------------
# run-local: sam local invoke
# ---------------------------------------------------------------------------


def cmd_run_local(flags: dict[str, Any]) -> int:
    """Ejecuta el lambda en local con `sam local invoke`.

    Regenera el SAM desde lambda.yaml y corre `sam local invoke` con el
    event JSON indicado (--event).
    """
    _ensure_tool(
        'sam',
        'Instalar: brew install aws-sam-cli  o  pip install aws-sam-cli',
    )
    resolved = _require_lambda_controller(flags)
    stage = flags.get('stage', 'local')
    # `local` no es un stage de env vars; usamos dev para el bloque de env.
    env_stage = 'dev' if stage == 'local' else stage

    try:
        _regenerate_sam(resolved, env_stage)
    except ManifestError as exc:
        _err(str(exc))
        return 1

    args = ['sam', 'local', 'invoke']

    event = flags.get('event')
    if event:
        event_path = (resolved.root / event).resolve()
        if not event_path.is_file():
            _err(f'Event JSON no existe: {event_path}')
            return 1
        args.extend(['--event', str(event_path)])

    if flags.get('debug'):
        args.append('--debug')

    return _run(args, cwd=resolved.root)


# ---------------------------------------------------------------------------
# deploy: sam build + sam deploy
# ---------------------------------------------------------------------------


def cmd_deploy_lambda(flags: dict[str, Any]) -> int:
    """Deploya un lambda-controller a un stage (sam build + sam deploy)."""
    _ensure_tool(
        'sam',
        'Instalar: brew install aws-sam-cli  o  pip install aws-sam-cli',
    )
    resolved = _require_lambda_controller(flags)
    stage = flags.get('stage', 'dev')

    if stage == 'local':
        _err('Stage `local` no se deploya — usa `run-local`')
        return 1

    try:
        _regenerate_sam(resolved, stage)
    except ManifestError as exc:
        _err(str(exc))
        return 1

    if flags.get('dry_run'):
        print(_c(YELLOW, f'[dry-run] sam build + sam deploy stage {stage}'))
        return 0

    build_rc = _run(['sam', 'build', '--use-container'], cwd=resolved.root)
    if build_rc != 0:
        _err('sam build fallo')
        return build_rc

    deploy_args = [
        'sam',
        'deploy',
        '--stack-name',
        f'{resolved.manifest["name"]}-{stage}',
        '--resolve-s3',
        '--capabilities',
        'CAPABILITY_IAM',
        '--no-confirm-changeset',
        '--region',
        str(resolved.manifest.get('region', 'us-east-1')),
    ]
    if flags.get('guided'):
        deploy_args.append('--guided')

    print(_c(YELLOW, f'Deploy de {resolved.manifest["name"]} a {stage}...'))
    return _run(deploy_args, cwd=resolved.root)


# ---------------------------------------------------------------------------
# invoke-remote: aws lambda invoke contra un stage deployado
# ---------------------------------------------------------------------------


def cmd_invoke_remote(flags: dict[str, Any]) -> int:
    """Invoca el lambda YA deployado en un stage (aws lambda invoke)."""
    _ensure_tool(
        'aws',
        'Instalar: brew install awscli  o  pip install awscli',
    )
    resolved = _require_lambda_controller(flags)
    stage = flags.get('stage', 'dev')

    if stage == 'local':
        _err('Stage `local` no esta deployado — usa `run-local`')
        return 1

    function_name = f'{resolved.manifest["name"]}-{stage}'
    region = str(resolved.manifest.get('region', 'us-east-1'))

    args = [
        'aws',
        'lambda',
        'invoke',
        '--function-name',
        function_name,
        '--region',
        region,
        '--cli-binary-format',
        'raw-in-base64-out',
    ]

    event = flags.get('event')
    if event:
        event_path = (resolved.root / event).resolve()
        if not event_path.is_file():
            _err(f'Event JSON no existe: {event_path}')
            return 1
        args.extend(['--payload', f'file://{event_path}'])

    out_path = resolved.root / '.aws-sam' / 'invoke-response.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args.append(str(out_path))

    rc = _run(args, cwd=resolved.root)
    if rc == 0 and out_path.is_file():
        print(_c(GREEN, f'Respuesta de {function_name}:'))
        try:
            payload = json.loads(out_path.read_text(encoding='utf-8'))
            print(json.dumps(payload, indent=2, default=str))
        except (json.JSONDecodeError, OSError):
            print(out_path.read_text(encoding='utf-8'))
    return rc


# ---------------------------------------------------------------------------
# Tests dinamicos (lambda-controller con tests/unit y tests/integration)
# ---------------------------------------------------------------------------


def _run_pytest(resolved: ResolvedLambda, subdir: str, flags: dict) -> int:
    """Corre pytest sobre tests/<subdir> con cwd en la raiz del lambda."""
    tests_dir = resolved.root / 'tests' / subdir
    if not tests_dir.is_dir():
        _err(f'No existe {tests_dir}')
        print(
            f'  Un lambda-controller debe traer tests/{subdir}/ '
            f'(ver el formato lambda-controller).',
        )
        return 1

    args = ['pytest', f'tests/{subdir}']
    if flags.get('verbose') or flags.get('v'):
        args.append('-v')
    if flags.get('quiet'):
        args.append('-q')

    return _run(args, cwd=resolved.root)


def cmd_test_unit_lambda(flags: dict[str, Any]) -> int:
    """pytest tests/unit del lambda-controller (cwd = raiz del lambda)."""
    resolved = _require_lambda_controller(flags)
    return _run_pytest(resolved, 'unit', flags)


def cmd_test_integration_lambda(flags: dict[str, Any]) -> int:
    """pytest tests/integration del lambda-controller."""
    resolved = _require_lambda_controller(flags)
    return _run_pytest(resolved, 'integration', flags)
