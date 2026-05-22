"""Deploy de los recursos compartidos del backend serverless.

Los recursos compartidos del backend (API Gateway REST, tablas DynamoDB,
DLQ SQS) viven como templates CloudFormation autonomos en
`serverless/lambda/resources/<tipo>/<nombre>.yaml`. Cada uno es un
template COMPLETO (con `AWSTemplateFormatVersion`, `Parameters`,
`Resources` y `Outputs`) y se deploya como un stack independiente
`portfolio-<tipo>-<nombre>-<stage>`.

Cada stack publica sus identificadores (ARN, name, stream-arn, ...) en
SSM Parameter Store con la convencion
`/portfolio/{stage}/{tipo}/{nombre}/{atributo}`. Los Lambdas leen esos
parametros en el cold start, en vez de `Fn::ImportValue` — eso desacopla
los stacks: un recurso se puede redeployar sin bloquear los Lambdas.

Comandos:
  - `deploy-resource --name=<tipo>/<nombre> --stage=<env>`: deploya UN
    stack de recurso.
  - `destroy-resource --name=<tipo>/<nombre> --stage=<env> --confirm`:
    borra un stack de recurso (destructivo).
  - `deploy-infra --stage=<env>`: deploya TODOS los stacks de recurso.
  - `list-resources`: lista los recursos declarados en `resources/`.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from shared.console import CYAN
from shared.console import GREEN
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


# Raiz del backend serverless del portfolio.
_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'

# Directorio de los recursos compartidos (un template autonomo por recurso).
_RESOURCES_DIR = _SERVERLESS_DIR / 'lambda' / 'resources'

# Subdirectorios de _RESOURCES_DIR que contienen templates de recursos.
_RESOURCE_TYPES = ('dynamodb', 'api_gateway', 'sqs')

_REGION = 'us-east-1'


def _collect_resources() -> list[tuple[str, str, Path]]:
    """Devuelve los recursos declarados como (tipo, nombre, path).

    Un recurso es cualquier `.yaml` dentro de los subdirectorios de
    `_RESOURCES_DIR` (`dynamodb/`, `api_gateway/`, `sqs/`). El
    `_header.yaml` (documentacion del patron) NO es un recurso.
    """
    resources: list[tuple[str, str, Path]] = []
    for resource_type in _RESOURCE_TYPES:
        directory = _RESOURCES_DIR / resource_type
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob('*.yaml')):
            if path.stem.startswith('_'):
                continue
            resources.append((resource_type, path.stem, path))
    return resources


def _resolve_resource(name: str) -> tuple[str, str, Path]:
    """Resuelve `--name=<tipo>/<nombre>` a (tipo, nombre, path del template).

    Raises
    ------
    ValueError
        Si `name` no tiene la forma `<tipo>/<nombre>` o no existe.
    """
    if '/' not in name:
        raise ValueError(
            f'--name debe tener la forma <tipo>/<nombre> (recibido: {name!r}). '
            f'Ej: --name=dynamodb/contacts.',
        )
    resource_type, resource_name = name.split('/', 1)
    template = _RESOURCES_DIR / resource_type / f'{resource_name}.yaml'
    if not template.is_file():
        valid = ', '.join(f'{t}/{n}' for t, n, _ in _collect_resources())
        raise ValueError(
            f'No existe el recurso {name!r} en {_RESOURCES_DIR}. '
            f'Recursos validos: {valid}.',
        )
    return resource_type, resource_name, template


def _stack_name(resource_type: str, resource_name: str, stage: str) -> str:
    """Nombre del stack CloudFormation de un recurso."""
    return f'portfolio-{resource_type}-{resource_name}-{stage}'


def _aws(
    args: list[str], *, profile: str | None
) -> subprocess.CompletedProcess:
    """Ejecuta un comando `aws` y devuelve el CompletedProcess."""
    cmd = ['aws', *args]
    if profile:
        cmd += ['--profile', profile]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _deploy_one(
    resource_type: str,
    resource_name: str,
    template: Path,
    stage: str,
    *,
    profile: str | None,
    dry_run: bool,
) -> int:
    """Deploya UN stack de recurso. Devuelve el exit code."""
    stack = _stack_name(resource_type, resource_name, stage)

    if dry_run:
        print(_c(YELLOW, f'[dry-run] cloudformation deploy {stack}'))
        return 0

    deploy_cmd = [
        'cloudformation',
        'deploy',
        '--template-file',
        str(template),
        '--stack-name',
        stack,
        '--parameter-overrides',
        f'Stage={stage}',
        '--capabilities',
        'CAPABILITY_NAMED_IAM',
        '--region',
        _REGION,
        '--no-fail-on-empty-changeset',
    ]
    print(_c(YELLOW, f'Deploy de {stack}...'))
    result = _aws(deploy_cmd, profile=profile)
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        _err(f'Deploy de {stack} fallo:\n{result.stderr.strip()}')
        return result.returncode
    print(_c(GREEN, f'OK  stack {stack} desplegado'))
    return 0


def cmd_deploy_resource(flags: dict[str, Any]) -> int:
    """Deploya UN stack de recurso compartido.

    Flags:
      --name        : <tipo>/<nombre> (ej. dynamodb/contacts).
      --stage       : dev | stage | prod (default dev).
      --aws-profile : perfil AWS CLI (opcional).
      --dry-run     : muestra que haria sin ejecutar.
    """
    stage = flags.get('stage', 'dev')
    if stage == 'local':
        _err('Los recursos compartidos no aplican al stage `local`.')
        return 1

    name = flags.get('name')
    if not name:
        _err('deploy-resource requiere --name=<tipo>/<nombre>.')
        return 2

    try:
        resource_type, resource_name, template = _resolve_resource(name)
    except ValueError as exc:
        _err(str(exc))
        return 1

    return _deploy_one(
        resource_type,
        resource_name,
        template,
        stage,
        profile=flags.get('aws_profile'),
        dry_run=bool(flags.get('dry_run')),
    )


def cmd_destroy_resource(flags: dict[str, Any]) -> int:
    """Borra un stack de recurso compartido (DESTRUCTIVO).

    Flags:
      --name        : <tipo>/<nombre>.
      --stage       : dev | stage | prod.
      --confirm     : obligatorio (operacion destructiva).
      --aws-profile : perfil AWS CLI (opcional).
    """
    stage = flags.get('stage', 'dev')
    if stage == 'local':
        _err('Los recursos compartidos no aplican al stage `local`.')
        return 1

    name = flags.get('name')
    if not name:
        _err('destroy-resource requiere --name=<tipo>/<nombre>.')
        return 2

    if not flags.get('confirm'):
        _err('destroy-resource es destructivo: agrega --confirm.')
        return 2

    try:
        resource_type, resource_name, _ = _resolve_resource(name)
    except ValueError as exc:
        _err(str(exc))
        return 1

    stack = _stack_name(resource_type, resource_name, stage)
    profile = flags.get('aws_profile')

    if flags.get('dry_run'):
        print(_c(YELLOW, f'[dry-run] cloudformation delete-stack {stack}'))
        return 0

    print(_c(YELLOW, f'Borrando stack {stack}...'))
    result = _aws(
        [
            'cloudformation',
            'delete-stack',
            '--stack-name',
            stack,
            '--region',
            _REGION,
        ],
        profile=profile,
    )
    if result.returncode != 0:
        _err(f'No se pudo borrar {stack}:\n{result.stderr.strip()}')
        return result.returncode
    print(_c(GREEN, f'OK  stack {stack} en borrado'))
    return 0


def cmd_deploy_infra(flags: dict[str, Any]) -> int:
    """Deploya TODOS los stacks de recurso compartido de `resources/`.

    Itera los templates de `resources/` y deploya un stack por cada uno.
    Ya no ensambla un stack unico: cada recurso es autonomo.

    Flags:
      --stage       : dev | stage | prod (default dev).
      --aws-profile : perfil AWS CLI (opcional).
      --dry-run     : muestra que haria sin ejecutar.
    """
    stage = flags.get('stage', 'dev')
    if stage == 'local':
        _err('Los recursos compartidos no aplican al stage `local`.')
        return 1

    resources = _collect_resources()
    if not resources:
        _err(f'No hay recursos en {_RESOURCES_DIR}.')
        return 1

    profile = flags.get('aws_profile')
    dry_run = bool(flags.get('dry_run'))
    rc = 0
    for resource_type, resource_name, template in resources:
        rc = (
            _deploy_one(
                resource_type,
                resource_name,
                template,
                stage,
                profile=profile,
                dry_run=dry_run,
            )
            or rc
        )
    return rc


def cmd_list_resources(flags: dict[str, Any]) -> int:
    """Lista los recursos compartidos declarados en `resources/`."""
    resources = _collect_resources()
    if not resources:
        print(_c(YELLOW, f'No hay recursos en {_RESOURCES_DIR}.'))
        return 0

    stage = flags.get('stage', 'dev')
    print(_c(CYAN, f'Recursos compartidos (stage {stage}):'))
    for resource_type, resource_name, _ in resources:
        stack = _stack_name(resource_type, resource_name, stage)
        print(f'  {resource_type}/{resource_name}  ->  {stack}')
    return 0
