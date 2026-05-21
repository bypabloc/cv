"""Deploy del stack de infra compartida del backend serverless.

El backend del portfolio son 5 stacks CloudFormation independientes (ver
`serverless/infra/infra.yaml`): un stack de infra compartida + un stack
por Lambda. Este modulo deploya el stack de infra.

`infra.yaml` declara 5 tablas DynamoDB, una API Gateway REST y una DLQ.
El deploy es IDEMPOTENTE:
  - Si el stack no existe -> lo crea (CREATE).
  - Si ya existe -> aplica los cambios (UPDATE); CloudFormation detecta
    si el modelado cambio y actualiza solo lo necesario.
  - Antes de crear, verifica si las tablas del manifiesto ya existen
    como recursos sueltos en AWS (fuera de CloudFormation) y avisa: una
    tabla preexistente fuera del stack haria fallar el CREATE.
"""

from __future__ import annotations

import json
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

# Template del stack de infra (versionado, NO se genera).
_INFRA_TEMPLATE = _SERVERLESS_DIR / 'infra' / 'infra.yaml'

# Tablas DynamoDB que declara infra.yaml (para el chequeo de pre-existencia).
_INFRA_TABLES = (
    'portfolio-contacts-${stage}',
    'portfolio-tracking-${stage}',
    'portfolio-cache-${stage}',
    'portfolio-rate-limit-rules-${stage}',
    'portfolio-rate-limit-buckets-${stage}',
)


def _aws(
    args: list[str], *, profile: str | None
) -> subprocess.CompletedProcess:
    """Ejecuta un comando `aws` y devuelve el CompletedProcess."""
    cmd = ['aws', *args]
    if profile:
        cmd += ['--profile', profile]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _stack_exists(stack: str, region: str, profile: str | None) -> bool:
    """True si el stack CloudFormation ya existe."""
    result = _aws(
        [
            'cloudformation',
            'describe-stacks',
            '--stack-name',
            stack,
            '--region',
            region,
        ],
        profile=profile,
    )
    return result.returncode == 0


def _table_exists(table: str, region: str, profile: str | None) -> bool:
    """True si una tabla DynamoDB ya existe en la cuenta."""
    result = _aws(
        [
            'dynamodb',
            'describe-table',
            '--table-name',
            table,
            '--region',
            region,
        ],
        profile=profile,
    )
    return result.returncode == 0


def _table_in_stack(
    table: str, stack: str, region: str, profile: str | None
) -> bool:
    """True si la tabla pertenece al stack de infra (no es huerfana)."""
    result = _aws(
        [
            'cloudformation',
            'describe-stack-resources',
            '--stack-name',
            stack,
            '--region',
            region,
        ],
        profile=profile,
    )
    if result.returncode != 0:
        return False
    try:
        resources = json.loads(result.stdout).get('StackResources', [])
    except json.JSONDecodeError:
        return False
    return any(
        r.get('PhysicalResourceId') == table
        and r.get('ResourceType') == 'AWS::DynamoDB::Table'
        for r in resources
    )


def _preflight_tables(
    stage: str, region: str, stack: str, profile: str | None
) -> bool:
    """Verifica el estado de las tablas antes de un CREATE del stack.

    Reporta, por cada tabla declarada en infra.yaml:
      - no existe          -> el stack la creara (OK).
      - existe en el stack -> el stack la actualizara (OK).
      - existe huerfana    -> el CREATE del stack fallaria (BLOQUEA).

    Returns
    -------
    bool
        True si el deploy puede proceder; False si hay una tabla
        huerfana que bloquearia el CREATE.
    """
    print(_c(CYAN, 'Verificando tablas DynamoDB declaradas en infra.yaml:'))
    blocked = False
    for tpl in _INFRA_TABLES:
        table = tpl.replace('${stage}', stage)
        if not _table_exists(table, region, profile):
            print(_c(GREEN, f'  [crear]   {table} — no existe'))
        elif _table_in_stack(table, stack, region, profile):
            print(_c(CYAN, f'  [existe]  {table} — ya en el stack'))
        else:
            print(
                _c(
                    YELLOW,
                    f'  [HUERFANA] {table} — existe fuera de {stack}. '
                    f'El CREATE del stack fallaria.',
                )
            )
            blocked = True
    return not blocked


def cmd_deploy_infra(flags: dict[str, Any]) -> int:
    """Deploya el stack de infra compartida (idempotente).

    Flags:
      --stage   : dev | stage | prod (default dev).
      --profile : perfil AWS CLI (opcional).
      --dry-run : muestra que haria sin ejecutar.
    """
    stage = flags.get('stage', 'dev')
    if stage == 'local':
        _err('El stack de infra no aplica al stage `local`.')
        return 1

    profile = flags.get('profile')
    region = 'us-east-1'
    stack = f'portfolio-infra-{stage}'

    if not _INFRA_TEMPLATE.is_file():
        _err(f'No existe el template de infra: {_INFRA_TEMPLATE}')
        return 1

    exists = _stack_exists(stack, region, profile)
    action = 'UPDATE' if exists else 'CREATE'
    print(
        _c(
            CYAN,
            f'Stack {stack}: {"ya existe" if exists else "no existe"} '
            f'-> {action}',
        )
    )

    # Pre-chequeo de tablas solo en CREATE (en UPDATE ya estan en el stack).
    if not exists and not _preflight_tables(stage, region, stack, profile):
        _err(
            'Hay tablas que existen fuera del stack de infra. '
            'Importalas al stack o eliminalas antes de crear el stack.',
        )
        return 1

    if flags.get('dry_run'):
        print(_c(YELLOW, f'[dry-run] cloudformation deploy {stack}'))
        return 0

    deploy_cmd = [
        'cloudformation',
        'deploy',
        '--template-file',
        str(_INFRA_TEMPLATE),
        '--stack-name',
        stack,
        '--parameter-overrides',
        f'Stage={stage}',
        '--capabilities',
        'CAPABILITY_NAMED_IAM',
        '--region',
        region,
        '--no-fail-on-empty-changeset',
    ]
    print(_c(YELLOW, f'Deploy de infra a {stage}...'))
    result = _aws(deploy_cmd, profile=profile)
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        _err(f'Deploy de infra fallo:\n{result.stderr.strip()}')
        return result.returncode

    print(_c(GREEN, f'OK  stack {stack} desplegado'))
    return 0
