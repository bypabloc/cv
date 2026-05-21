"""Configuracion pytest del Lambda `tracking_pixel`.

Agrega `core/` al `sys.path` para que los imports absolutos del codigo
(`handler`, `controllers.`, `services.`, `models.`, `settings.`,
`utils.`) resuelvan en los tests.

La libreria comun `shared/` normalmente se vendoriza en `core/shared/`
por devtools antes de correr los tests (`serverless test-unit` lo hace).
Si no esta vendorizada (pytest invocado directo), este conftest agrega
`serverless/` al path como fallback para que `import shared...` resuelva
desde la fuente maestra `serverless/shared/`.

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
# La fuente maestra vive en serverless/shared/ (serverless/ = parents[3]).
if not (_CORE / 'shared').is_dir():
    _SERVERLESS_ROOT = _LAMBDA_ROOT.parents[1]
    sys.path.insert(0, str(_SERVERLESS_ROOT))

# Env vars minimas para que AppConfig + shared.* carguen sin un entorno
# Lambda real. Se setean al import del conftest, antes de cualquier test.
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('STAGE', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('LOG_LEVEL', 'INFO')
os.environ.setdefault('TRACKING_TABLE_NAME', 'portfolio-tracking-test')
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
    """Setup AWS mock con tracking/cache/rate-limit tables.

    Crea las 4 tablas DynamoDB que el Lambda usa bajo `mock_aws()` y
    resetea el resource singleton de boto3 para que no quede apuntando a
    un mock de un test anterior.
    """
    import boto3
    from moto import mock_aws

    from shared.dynamodb_client import reset_resource_cache

    with mock_aws():
        # El resource DynamoDB singleton se recrea bajo este mock_aws():
        # si quedo cacheado de un test anterior apuntaria a otro mock.
        reset_resource_cache()
        ddb = boto3.client('dynamodb', region_name='us-east-1')

        ddb.create_table(
            TableName='portfolio-tracking-test',
            AttributeDefinitions=[
                {'AttributeName': 'session_id', 'AttributeType': 'S'},
                {'AttributeName': 'page_id', 'AttributeType': 'S'},
            ],
            KeySchema=[
                {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                {'AttributeName': 'page_id', 'KeyType': 'RANGE'},
            ],
            BillingMode='PAY_PER_REQUEST',
        )
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
