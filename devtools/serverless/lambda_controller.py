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

from serverless.packaging import PackagingError
from serverless.packaging import packaged_lambda
from serverless.resolve import ManifestError
from serverless.resolve import ResolvedLambda
from serverless.resolve import resolve_lambda
from serverless.sam_generate import generate_sam_file
from serverless.vendoring import VendoringError
from serverless.vendoring import vendored_shared
from shared.console import CYAN
from shared.console import GREEN
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


# Python del `.venv` del backend serverless del portfolio. Tiene la union
# de las deps de runtime de los 4 lambdas (Powertools, pydantic, boto3,
# SQLAlchemy, etc.) — se usa para correr los tests de un lambda cuando
# este no trae su propio `.venv`.
_PORTFOLIO_SERVERLESS_VENV = (
    Path(__file__).resolve().parents[2]
    / 'serverless'
    / '.venv'
    / 'bin'
    / 'python'
)


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


def _regenerate_sam(
    resolved: ResolvedLambda,
    stage: str,
    *,
    code_uri: str = 'build',
) -> Path:
    """Regenera el template.yaml efimero del lambda para un stage.

    `code_uri` es el directorio del codigo: `build/` para deploy (el
    artefacto que devtools arma con uv) o `.` para run-local.
    """
    template = generate_sam_file(resolved, stage=stage, code_uri=code_uri)
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

    # run-local empaqueta con `core/shared/` vendorizado en la raiz del
    # lambda: el CodeUri del template apunta a `.`, no a `build/`.
    try:
        _regenerate_sam(resolved, env_stage, code_uri='.')
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

    # Vendoriza serverless/lambda/shared/ en core/shared/ para que el codigo del
    # lambda resuelva `import shared...` durante la invocacion local.
    try:
        with vendored_shared(resolved.root):
            return _run(args, cwd=resolved.root)
    except VendoringError as exc:
        _err(str(exc))
        return 1


# ---------------------------------------------------------------------------
# deploy: sam build + sam deploy
# ---------------------------------------------------------------------------


def cmd_deploy_lambda(flags: dict[str, Any]) -> int:
    """Deploya un lambda-controller a un stage.

    devtools arma el artefacto (`build/`) con uv: instala las deps del
    lambda + de los subpaquetes de `shared/` que usa, copia `core/` y
    vendoriza el cierre de subpaquetes resuelto. SAM solo deploya: el
    template apunta `CodeUri` a `build/` y, al no tener
    `Metadata.BuildMethod`, `sam deploy` zipea ese directorio tal cual
    sin correr `pip`.
    """
    _ensure_tool(
        'uv', 'Instalar: curl -LsSf https://astral.sh/uv/install.sh | sh'
    )
    _ensure_tool(
        'sam',
        'Instalar: brew install aws-sam-cli  o  pip install aws-sam-cli',
    )
    resolved = _require_lambda_controller(flags)
    stage = flags.get('stage', 'dev')

    if stage == 'local':
        _err('Stage `local` no se deploya — usa `run-local`')
        return 1

    # El template de deploy apunta CodeUri a build/ (el artefacto uv).
    try:
        _regenerate_sam(resolved, stage, code_uri='build')
    except ManifestError as exc:
        _err(str(exc))
        return 1

    if flags.get('dry_run'):
        print(_c(YELLOW, f'[dry-run] uv package + sam deploy stage {stage}'))
        return 0

    stack_name = f'portfolio-{resolved.manifest["name"]}-{stage}'
    deploy_args = [
        'sam',
        'deploy',
        '--stack-name',
        stack_name,
        '--resolve-s3',
        '--capabilities',
        'CAPABILITY_IAM',
        '--no-confirm-changeset',
        '--no-fail-on-empty-changeset',
        '--region',
        str(resolved.manifest.get('region', 'us-east-1')),
    ]
    aws_profile = flags.get('aws_profile')
    if aws_profile:
        deploy_args += ['--profile', str(aws_profile)]
    if flags.get('guided'):
        deploy_args.append('--guided')

    runtime = str(resolved.manifest['runtime'])
    print(_c(CYAN, f'Runtime del artefacto: {runtime}'))

    # devtools arma build/ con uv (deps + core/ + shared/ selectivo). El
    # build/ se limpia al salir del bloque (sam deploy ya lo subio).
    try:
        with packaged_lambda(resolved.root, runtime=runtime) as packaged:
            _, closure, all_deps = packaged
            print(
                _c(
                    CYAN,
                    f'Artefacto: shared/{{{", ".join(sorted(closure))}}} '
                    f'+ {len(all_deps)} deps',
                )
            )
            print(
                _c(
                    YELLOW,
                    f'Deploy de {resolved.manifest["name"]} a {stage}...',
                )
            )
            return _run(deploy_args, cwd=resolved.root)
    except PackagingError as exc:
        _err(str(exc))
        return 1


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

    # El FunctionName fisico lleva el prefijo `portfolio-` (ver
    # sam_generate.build_template) y el sufijo de stage.
    function_name = f'portfolio-{resolved.manifest["name"]}-{stage}'
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
    aws_profile = flags.get('aws_profile')
    if aws_profile:
        args += ['--profile', str(aws_profile)]

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


def _resolve_pytest_python(resolved: ResolvedLambda) -> str:
    """Resuelve el interprete Python para correr los tests del lambda.

    Los tests del lambda necesitan las deps de runtime (Powertools,
    pydantic, etc.) que el `.venv` de devtools NO tiene. Busca un `.venv`
    con esas deps, en orden:
      1. `<lambda>/.venv` (el propio lambda, si lo tiene).
      2. El `.venv` del backend serverless (`serverless/.venv`), que ya
         instala la union de deps de los 4 lambdas.
      3. `python3` del PATH (fallback; puede no tener las deps).
    """
    candidates = [
        resolved.root / '.venv' / 'bin' / 'python',
        _PORTFOLIO_SERVERLESS_VENV,
    ]
    for python in candidates:
        if python.is_file():
            return str(python)
    return 'python3'


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

    python = _resolve_pytest_python(resolved)
    args = [python, '-m', 'pytest', f'tests/{subdir}', '-o', 'addopts=']
    if flags.get('verbose') or flags.get('v'):
        args.append('-v')
    if flags.get('quiet'):
        args.append('-q')

    # Vendoriza serverless/lambda/shared/ en core/shared/ para que los tests
    # resuelvan `import shared...` igual que en el artefacto desplegado.
    try:
        with vendored_shared(resolved.root):
            return _run(args, cwd=resolved.root)
    except VendoringError as exc:
        _err(str(exc))
        return 1


def cmd_test_unit_lambda(flags: dict[str, Any]) -> int:
    """pytest tests/unit del lambda-controller (cwd = raiz del lambda)."""
    resolved = _require_lambda_controller(flags)
    return _run_pytest(resolved, 'unit', flags)


def cmd_test_integration_lambda(flags: dict[str, Any]) -> int:
    """pytest tests/integration del lambda-controller."""
    resolved = _require_lambda_controller(flags)
    return _run_pytest(resolved, 'integration', flags)
