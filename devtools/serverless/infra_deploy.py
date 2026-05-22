"""Deploy del stack de infra compartida del backend serverless.

Los recursos compartidos del backend (API Gateway REST, tablas DynamoDB,
DLQ SQS) viven como fragmentos YAML en `serverless/lambda/resources/`,
uno por recurso. Cada fragmento declara solo `Resources:` y `Outputs:`;
el header comun (`_header.yaml`) declara `AWSTemplateFormatVersion`,
`Transform`, `Description` y `Parameters`.

`cmd_deploy_infra` ENSAMBLA el header + todos los fragmentos en un
`infra.yaml` efimero (gitignored) y lo deploya como un unico stack
CloudFormation `portfolio-infra-<stage>`.

NOTA: este es el modelo de UN stack de infra. El rediseno a
stack-por-recurso + SSM (cada recurso un stack autonomo, sin Export)
esta documentado en `docs/specs/serverless-restructure/` y se
implementara en una rama aparte.

El deploy es IDEMPOTENTE:
  - Si el stack no existe -> lo crea (CREATE).
  - Si ya existe -> aplica los cambios (UPDATE).
  - Antes de un CREATE, verifica que las tablas no existan huerfanas.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from shared.console import CYAN
from shared.console import GREEN
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


# Raiz del backend serverless del portfolio.
_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'

# Directorio de los recursos compartidos (un fragmento YAML por recurso).
_RESOURCES_DIR = _SERVERLESS_DIR / 'lambda' / 'resources'

# Header comun del template ensamblado (sin Resources ni Outputs).
_HEADER_FILE = _RESOURCES_DIR / '_header.yaml'

# Subdirectorios de _RESOURCES_DIR que contienen fragmentos de recursos.
_FRAGMENT_DIRS = ('dynamodb', 'api_gateway', 'sqs')

# Tablas DynamoDB que declara la infra (para el chequeo de pre-existencia).
_INFRA_TABLES = (
    'portfolio-contacts-${stage}',
    'portfolio-tracking-${stage}',
    'portfolio-cache-${stage}',
    'portfolio-rate-limit-rules-${stage}',
    'portfolio-rate-limit-buckets-${stage}',
)


def _collect_fragments() -> list[Path]:
    """Devuelve los fragmentos YAML de recursos, ordenados por path.

    Un fragmento es cualquier `.yaml` dentro de los subdirectorios de
    `_RESOURCES_DIR` (dynamodb/, api_gateway/, sqs/). El `_header.yaml`
    y el `infra.yaml` legacy NO son fragmentos.
    """
    fragments: list[Path] = []
    for subdir in _FRAGMENT_DIRS:
        directory = _RESOURCES_DIR / subdir
        if directory.is_dir():
            fragments.extend(sorted(directory.glob('*.yaml')))
    return fragments


def _assemble_template() -> str:
    """Ensambla el header + todos los fragmentos en un template unico.

    El resultado es un template CloudFormation valido: el header aporta
    `AWSTemplateFormatVersion` / `Transform` / `Description` /
    `Parameters`, y los fragmentos aportan, concatenados, sus bloques
    `Resources:` y `Outputs:`.

    Como cada fragmento ya trae `Resources:` y `Outputs:` como claves de
    nivel raiz, el ensamblado las fusiona: el primer fragmento abre cada
    bloque y los siguientes solo aportan entradas indentadas. Para
    mantenerlo simple y robusto, el ensamblado declara `Resources:` y
    `Outputs:` una sola vez y vuelca el cuerpo de cada fragmento debajo.

    Raises
    ------
    FileNotFoundError
        Si falta el header o no hay fragmentos.
    """
    if not _HEADER_FILE.is_file():
        raise FileNotFoundError(
            f'No existe el header de infra: {_HEADER_FILE}',
        )
    fragments = _collect_fragments()
    if not fragments:
        raise FileNotFoundError(
            f'No hay fragmentos de recursos en {_RESOURCES_DIR}.',
        )

    resources_body: list[str] = []
    outputs_body: list[str] = []
    for fragment in fragments:
        section = None
        for line in fragment.read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if stripped.startswith('#') or not stripped:
                # Comentarios y lineas vacias: solo dentro de una seccion.
                if section == 'resources':
                    resources_body.append(line)
                elif section == 'outputs':
                    outputs_body.append(line)
                continue
            if line.startswith('Resources:'):
                section = 'resources'
                continue
            if line.startswith('Outputs:'):
                section = 'outputs'
                continue
            if section == 'resources':
                resources_body.append(line)
            elif section == 'outputs':
                outputs_body.append(line)

    parts = [
        _HEADER_FILE.read_text(encoding='utf-8').rstrip(),
        '',
        'Resources:',
        *resources_body,
        '',
        'Outputs:',
        *outputs_body,
        '',
    ]
    return '\n'.join(parts)


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

    Reporta, por cada tabla declarada en los fragmentos:
      - no existe          -> el stack la creara (OK).
      - existe en el stack -> el stack la actualizara (OK).
      - existe huerfana    -> el CREATE del stack fallaria (BLOQUEA).

    Returns
    -------
    bool
        True si el deploy puede proceder; False si hay una tabla
        huerfana que bloquearia el CREATE.
    """
    print(_c(CYAN, 'Verificando tablas DynamoDB declaradas en resources/:'))
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

    Ensambla `_header.yaml` + los fragmentos de `resources/` en un
    `infra.yaml` efimero y lo deploya como `portfolio-infra-<stage>`.

    Flags:
      --stage       : dev | stage | prod (default dev).
      --aws-profile : perfil AWS CLI (opcional).
      --dry-run     : muestra que haria sin ejecutar.
    """
    stage = flags.get('stage', 'dev')
    if stage == 'local':
        _err('El stack de infra no aplica al stage `local`.')
        return 1

    profile = flags.get('aws_profile')
    region = 'us-east-1'
    stack = f'portfolio-infra-{stage}'

    try:
        template_body = _assemble_template()
    except FileNotFoundError as exc:
        _err(str(exc))
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
        print(_c(CYAN, '--- template ensamblado (resumen) ---'))
        print(template_body[:600])
        return 0

    # El template ensamblado es efimero: se escribe en un tmp y se borra
    # al salir. La fuente de verdad son los fragmentos de resources/.
    with tempfile.TemporaryDirectory() as tmp:
        template_path = Path(tmp) / 'infra.yaml'
        template_path.write_text(template_body, encoding='utf-8')

        deploy_cmd = [
            'cloudformation',
            'deploy',
            '--template-file',
            str(template_path),
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
