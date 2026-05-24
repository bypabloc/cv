"""Configuracion pytest del Lambda `tracking_pixel`.

Agrega `core/` al `sys.path` para que los imports absolutos del codigo
(`handler`, `controllers.`, `services.`, `models.`, `settings.`)
resuelvan en los tests.

La libreria comun `shared/` normalmente se vendoriza en `core/shared/`
por devtools antes de correr los tests (`serverless test-unit` lo hace).
Si no esta vendorizada (pytest invocado directo), este conftest agrega
`serverless/` al path como fallback para que `import shared...` resuelva
desde la fuente maestra `serverless/lambda/shared/`.

Setea las env vars minimas que `AppConfig` (settings/config.py) y las
libs de `shared/` necesitan, y mockea AWS para los tests unit (moto).
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# core/ al path: imports absolutos del codigo del Lambda.
_LAMBDA_ROOT = Path(__file__).resolve().parent.parent
_CORE = _LAMBDA_ROOT / 'core'
sys.path.insert(0, str(_CORE))

# Fallback para `import shared...` si no esta vendorizado en core/shared/.
# La fuente maestra shared/ vive en serverless/lambda/ (parents[1]:
# <lambda>/ -> services/ -> lambda/).
if not (_CORE / 'shared').is_dir():
    _LAMBDA_BASE = _LAMBDA_ROOT.parents[1]
    sys.path.insert(0, str(_LAMBDA_BASE))

# Env vars minimas para que AppConfig + shared.* carguen sin un entorno
# Lambda real. Se setean al import del conftest, antes de cualquier test.
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('STAGE', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('LOG_LEVEL', 'INFO')
# TRACKING_TABLE_NAME se elimino (spec direct-neon-writes): el Lambda
# ya no escribe a DynamoDB.tracking. La connection string de Neon va por
# el env var DATABASE_URL que mockeamos por test (no hace falta default
# aqui — los tests que persisten usan mock_neon_writes).
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost/test')
os.environ.setdefault('CACHE_TABLE_NAME', 'portfolio-cache-test')
os.environ.setdefault(
    'RATE_LIMIT_RULES_TABLE_NAME', 'portfolio-rate-limit-rules-test'
)
os.environ.setdefault(
    'RATE_LIMIT_BUCKETS_TABLE_NAME', 'portfolio-rate-limit-buckets-test'
)
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'tracking-pixel-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setea AWS credentials fake en todos los tests (autouse).

    Previene que boto3 lea ~/.aws/credentials reales o intente STS.
    Necesario para que moto interceptee las llamadas.
    """
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')


@pytest.fixture
def tracking_aws() -> Generator[None]:
    """Setup AWS mock con cache/rate-limit tables.

    Crea las 3 tablas DynamoDB que el Lambda usa bajo `mock_aws()` y
    resetea el resource singleton de boto3 para que no quede apuntando a
    un mock de un test anterior. La tabla `tracking` se elimino (spec
    direct-neon-writes): el Lambda escribe directo a Neon ahora —
    los tests de persistencia usan el fixture `mock_neon_writes`.
    """
    import boto3
    from moto import mock_aws
    from shared.aws.dynamodb import reset_resource_cache

    with mock_aws():
        # El resource DynamoDB singleton se recrea bajo este mock_aws():
        # si quedo cacheado de un test anterior apuntaria a otro mock.
        reset_resource_cache()
        ddb = boto3.client('dynamodb', region_name='us-east-1')

        ddb.create_table(
            TableName='portfolio-cache-test',
            AttributeDefinitions=[
                {'AttributeName': 'cache_key', 'AttributeType': 'S'},
            ],
            KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
            BillingMode='PAY_PER_REQUEST',
        )
        ddb.create_table(
            TableName='portfolio-rate-limit-rules-test',
            AttributeDefinitions=[
                {'AttributeName': 'rule_key', 'AttributeType': 'S'},
                {'AttributeName': 'kind', 'AttributeType': 'S'},
            ],
            KeySchema=[
                {'AttributeName': 'rule_key', 'KeyType': 'HASH'},
                {'AttributeName': 'kind', 'KeyType': 'RANGE'},
            ],
            BillingMode='PAY_PER_REQUEST',
        )
        ddb.create_table(
            TableName='portfolio-rate-limit-buckets-test',
            AttributeDefinitions=[
                {'AttributeName': 'bucket_key', 'AttributeType': 'S'},
            ],
            KeySchema=[{'AttributeName': 'bucket_key', 'KeyType': 'HASH'}],
            BillingMode='PAY_PER_REQUEST',
        )

        yield


@pytest.fixture
def mock_neon_writes(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Mockea `db_session()` + `insert_tracking()` y captura los payloads.

    Reemplaza la escritura real a Neon por un mock que registra los
    payloads pasados a `insert_tracking`. Devuelve la lista de payloads
    capturados para que los tests hagan asserts EXACTOS sobre lo que el
    service intento escribir.

    Spec `direct-neon-writes`: el Lambda escribe directo a Neon en vez
    de DynamoDB+Stream. En unit tests no levantamos un Postgres real —
    mockeamos el repository y verificamos que se llamo con el payload
    esperado.
    """
    from contextlib import contextmanager

    captured: list[dict] = []

    @contextmanager
    def _fake_db_session():
        yield object()  # Session falso — no se usa, solo se pasa al repo

    def _fake_insert_tracking(_session: object, payload: dict) -> None:
        captured.append(payload)

    # `db_session` esta importado en `services.tracking_service` con
    # `from shared.db.session import db_session` — parchamos AHI (donde se
    # usa), no en `shared.db.session` (donde se define) para que el
    # rebind funcione.
    monkeypatch.setattr(
        'services.tracking_service.db_session', _fake_db_session
    )
    monkeypatch.setattr(
        'services.tracking_service.insert_tracking', _fake_insert_tracking
    )
    return captured
