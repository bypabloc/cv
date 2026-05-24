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


_STUB_VISIT_ID = '019e5c50-0000-7000-8000-000000000001'
"""visit_id determinista (UUIDv7 valido) que el mock de
`ensure_session_and_visit` retorna. Lo usan asserts de tests."""


@pytest.fixture
def session_visit_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Captura los kwargs de cada invocacion a `ensure_session_and_visit`.

    Retorna un visit_id determinista (`_STUB_VISIT_ID`) para que los
    asserts de tests downstream sean predecibles. Mockea el helper en
    `services.tracking_service` (donde se importa).

    Spec sessions-normalize: el service ahora UPSERTea session + visit
    via este helper antes del INSERT de tracking_events. Los tests
    verifican QUE ARGS recibio el helper — el comportamiento real del
    helper (idempotencia, visit-trigger) se valida en sus propios
    tests / integration.
    """
    captured: list[dict] = []

    def _fake_ensure(_session: object, **kwargs: object) -> tuple[str, str]:
        captured.append(dict(kwargs))
        return str(kwargs['session_id']), _STUB_VISIT_ID

    monkeypatch.setattr(
        'services.tracking_service.ensure_session_and_visit', _fake_ensure
    )
    return captured


@pytest.fixture
def mock_neon_writes(
    monkeypatch: pytest.MonkeyPatch,
    session_visit_calls: list[dict],
) -> list[dict]:
    """Mockea las 3 escrituras a Neon: db_session + ensure_session_and_visit
    (via `session_visit_calls`) + insert_tracking. Captura los payloads
    de `insert_tracking`.

    El `db_session()` yield un `object()` falso (no se usa porque los
    mocks downstream no tocan el session).

    Spec sessions-normalize: tests verifican el SHAPE del payload de
    `tracking_events` (sin ip/country/ua/utm — esos viven en sessions y
    session_visits). Si el test tambien quiere verificar los args del
    helper, agrega `session_visit_calls` como fixture explicito.
    """
    from contextlib import contextmanager

    # `session_visit_calls` se inyecta y registra el mock del helper.
    _ = session_visit_calls

    captured: list[dict] = []

    @contextmanager
    def _fake_db_session():
        yield object()  # Session falso — los mocks no lo usan.

    def _fake_insert_tracking(_session: object, payload: dict) -> None:
        captured.append(payload)

    monkeypatch.setattr(
        'services.tracking_service.db_session', _fake_db_session
    )
    monkeypatch.setattr(
        'services.tracking_service.insert_tracking', _fake_insert_tracking
    )
    return captured
