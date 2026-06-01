"""Comando `serverless seed-email-config`.

Sube los templates de email (`send_email/seeds/templates/*`) al bucket S3
`portfolio-email-templates-${stage}` y hace PutItem de las filas de
configuracion (`build_rows`) a la tabla DynamoDB
`portfolio-email-config-${stage}`. La Lambda `send_email` lee esas filas
en runtime para renderizar y enviar via SES.

La fuente de verdad de las filas + subjects es
`serverless/lambda/services/send_email/seeds/email_config.py` (Python
puro, sin deps externas): se carga por ruta de archivo para no duplicar
los subjects en devtools.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import importlib.util
import json
from pathlib import Path
from typing import Any

from serverless import aws_cli
from shared.console import CYAN
from shared.console import GREEN
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


_SERVERLESS_ROOT = Path(__file__).resolve().parents[2] / 'serverless'
_SEND_EMAIL_DIR = _SERVERLESS_ROOT / 'lambda' / 'services' / 'send_email'
_TEMPLATES_DIR = _SEND_EMAIL_DIR / 'seeds' / 'templates'
_EMAIL_CONFIG_PY = _SEND_EMAIL_DIR / 'seeds' / 'email_config.py'

# Stages que usan AWS (local inyecta env vars directo, no usa SSM/DDB/S3).
_AWS_STAGES = ('dev', 'stage', 'prod')


@dataclass(frozen=True)
class _Upload:
    """Un template a subir: archivo local -> key en el bucket."""

    local_path: Path
    s3_key: str


@dataclass(frozen=True)
class SeedPlan:
    """Plan de seed: bucket, tabla y la lista de uploads + filas."""

    bucket: str
    table: str
    uploads: list[_Upload] = field(default_factory=list)
    rows: list[dict[str, str]] = field(default_factory=list)


def _load_build_rows() -> Any:
    """Carga `build_rows` desde el `email_config.py` del Lambda send_email."""
    spec = importlib.util.spec_from_file_location(
        '_send_email_seeds_email_config', _EMAIL_CONFIG_PY
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f'no se pudo cargar {_EMAIL_CONFIG_PY}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_rows


def build_seed_plan(*, stage: str) -> SeedPlan:
    """Construye el plan de seed para un stage (funcion pura).

    Resuelve el bucket/tabla por convencion (mismo nombre fisico que los
    `resources/{s3,dynamodb}/*.yaml`), lista los uploads de template
    (`<kind>.html` / `<kind>.txt` -> mismo nombre como key) y arma las
    filas de email-config con `build_rows(bucket)`.
    """
    bucket = f'portfolio-email-templates-{stage}'
    table = f'portfolio-email-config-{stage}'

    rows = list(_load_build_rows()(bucket))

    uploads: list[_Upload] = [
        _Upload(local_path=_TEMPLATES_DIR / key, s3_key=key)
        for row in rows
        for key in (row['html_path'], row['txt_path'])
    ]

    return SeedPlan(bucket=bucket, table=table, uploads=uploads, rows=rows)


def _put_item_args(table: str, row: dict[str, str]) -> list[str]:
    """Argumentos de `aws dynamodb put-item` para una fila (todos S)."""
    item = {k: {'S': str(v)} for k, v in row.items()}
    return [
        'dynamodb',
        'put-item',
        '--table-name',
        table,
        '--item',
        json.dumps(item),
    ]


def cmd_seed_email_config(flags: dict[str, Any]) -> int:
    """Sube templates a S3 + PutItem de las filas a `email-config`.

    Idempotente: `s3 cp` sobreescribe; `put-item` reemplaza la fila (PK
    `kind`). Requiere que el bucket y la tabla ya existan (los provisiona
    `provision-infra`).
    """
    stage = str(flags.get('stage', 'dev'))
    profile = flags.get('aws_profile')
    profile_str = str(profile) if profile else None

    if stage not in _AWS_STAGES:
        _err(
            f'seed-email-config no aplica al stage {stage!r} '
            f'(usa uno de {list(_AWS_STAGES)}).'
        )
        return 1

    plan = build_seed_plan(stage=stage)

    bucket_exists = aws_cli.aws_resource_exists(
        's3api',
        ['head-bucket', '--bucket', plan.bucket],
        profile=profile_str,
    )
    if not bucket_exists:
        _err(
            f'el bucket {plan.bucket} no existe — corre primero '
            f'`serverless provision-infra --stage={stage}`.'
        )
        return 1

    table_exists = aws_cli.aws_resource_exists(
        'dynamodb',
        ['describe-table', '--table-name', plan.table],
        profile=profile_str,
    )
    if not table_exists:
        _err(
            f'la tabla {plan.table} no existe — corre primero '
            f'`serverless provision-infra --stage={stage}`.'
        )
        return 1

    print(_c(CYAN, f'Seed email-config (stage {stage}):'))

    for upload in plan.uploads:
        if not upload.local_path.is_file():
            _err(f'template faltante: {upload.local_path}')
            return 1
        aws_cli.aws(
            [
                's3',
                'cp',
                str(upload.local_path),
                f's3://{plan.bucket}/{upload.s3_key}',
            ],
            profile=profile_str,
        )
    print(_c(GREEN, f'  OK  {len(plan.uploads)} templates -> {plan.bucket}'))

    for row in plan.rows:
        aws_cli.aws(
            _put_item_args(plan.table, row),
            profile=profile_str,
        )
    print(_c(GREEN, f'  OK  {len(plan.rows)} filas -> {plan.table}'))

    print(_c(YELLOW, 'seed-email-config completado.'))
    return 0
