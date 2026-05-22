"""Fixtures de los integration tests de la libreria comun `shared`.

A diferencia de los unit tests (`tests/unit/`), aqui NO se mockean los
modulos propios: el codigo de `shared/` corre contra recursos AWS
emulados por `moto` (`mock_aws`) — DynamoDB, SES, SSM/KMS — y contra
httpx interceptado por `respx` (Turnstile). El objetivo es ejercitar el
roundtrip completo de cada subpaquete.

Convenciones:
- Los recursos AWS los crea cada fixture DENTRO de un `mock_aws()` activo.
- El resource boto3 singleton de `shared.aws.dynamodb` se recrea con
  `reset_resource_cache()` bajo cada `mock_aws()` para que `moto`
  intercepte.
- Las env vars (nombres de tabla) se setean con `monkeypatch` y apuntan a
  las tablas `*-it` (integration tests) para no chocar con las `*-test`
  de los unit tests.
- El conftest raiz (`tests/conftest.py`) ya provee `aws_credentials`,
  `reset_settings_cache` y agrega `serverless/lambda/` al `sys.path`.
"""

from __future__ import annotations

from collections.abc import Generator

import boto3
import pytest
from moto import mock_aws
from shared.aws.dynamodb import reset_resource_cache

# Nombres de tabla para integration tests. Distintos de los `*-test` que
# usan los unit tests, para que un cambio en uno no afecte al otro.
CONTACTS_TABLE = 'portfolio-contacts-it'
TRACKING_TABLE = 'portfolio-tracking-it'
CACHE_TABLE = 'portfolio-cache-it'
RATE_LIMIT_RULES_TABLE = 'portfolio-rate-limit-rules-it'
RATE_LIMIT_BUCKETS_TABLE = 'portfolio-rate-limit-buckets-it'


@pytest.fixture(autouse=True)
def integration_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Apunta cada modelo del ORM a su tabla `*-it` (autouse).

    Setea SOLO los `table_env_var` (nombre literal). NO setea los
    `table_ssm_env` (`SSM_*_TABLE_PATH`): asi `BaseModel.table_name()`
    cae al `table_env_var` y no intenta resolver via SSM.
    """
    monkeypatch.setenv('CONTACTS_TABLE_NAME', CONTACTS_TABLE)
    monkeypatch.setenv('TRACKING_TABLE_NAME', TRACKING_TABLE)
    monkeypatch.setenv('CACHE_TABLE_NAME', CACHE_TABLE)
    monkeypatch.setenv('RATE_LIMIT_RULES_TABLE_NAME', RATE_LIMIT_RULES_TABLE)
    monkeypatch.setenv(
        'RATE_LIMIT_BUCKETS_TABLE_NAME', RATE_LIMIT_BUCKETS_TABLE
    )


def _create_cache_table(client: object) -> None:
    """Crea la tabla cache (PK `cache_key`, TTL `expires_at`)."""
    client.create_table(  # type: ignore[attr-defined]
        TableName=CACHE_TABLE,
        AttributeDefinitions=[
            {'AttributeName': 'cache_key', 'AttributeType': 'S'},
        ],
        KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
        BillingMode='PAY_PER_REQUEST',
    )
    client.update_time_to_live(  # type: ignore[attr-defined]
        TableName=CACHE_TABLE,
        TimeToLiveSpecification={
            'Enabled': True,
            'AttributeName': 'expires_at',
        },
    )


def _create_rate_limit_tables(client: object) -> None:
    """Crea las 2 tablas de rate-limit (rules + buckets)."""
    client.create_table(  # type: ignore[attr-defined]
        TableName=RATE_LIMIT_RULES_TABLE,
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
    client.update_time_to_live(  # type: ignore[attr-defined]
        TableName=RATE_LIMIT_RULES_TABLE,
        TimeToLiveSpecification={
            'Enabled': True,
            'AttributeName': 'expires_at',
        },
    )
    client.create_table(  # type: ignore[attr-defined]
        TableName=RATE_LIMIT_BUCKETS_TABLE,
        AttributeDefinitions=[
            {'AttributeName': 'bucket_key', 'AttributeType': 'S'},
        ],
        KeySchema=[{'AttributeName': 'bucket_key', 'KeyType': 'HASH'}],
        BillingMode='PAY_PER_REQUEST',
    )
    client.update_time_to_live(  # type: ignore[attr-defined]
        TableName=RATE_LIMIT_BUCKETS_TABLE,
        TimeToLiveSpecification={
            'Enabled': True,
            'AttributeName': 'expires_at',
        },
    )


@pytest.fixture
def cache_table() -> Generator[str]:
    """Levanta `mock_aws` con la tabla cache; cede el nombre fisico."""
    with mock_aws():
        reset_resource_cache()
        client = boto3.client('dynamodb', region_name='us-east-1')
        _create_cache_table(client)
        yield CACHE_TABLE
        reset_resource_cache()


@pytest.fixture
def rate_limit_tables() -> Generator[dict[str, str]]:
    """Levanta `mock_aws` con las 3 tablas que usa rate-limit.

    Incluye `cache` porque `rate_limit/rules.py` cachea las rules con el
    decorator `@cached`, que persiste en la tabla cache.
    """
    with mock_aws():
        reset_resource_cache()
        client = boto3.client('dynamodb', region_name='us-east-1')
        _create_cache_table(client)
        _create_rate_limit_tables(client)
        yield {
            'cache': CACHE_TABLE,
            'rules': RATE_LIMIT_RULES_TABLE,
            'buckets': RATE_LIMIT_BUCKETS_TABLE,
        }
        reset_resource_cache()


@pytest.fixture
def dynamodb_tables() -> Generator[None]:
    """Levanta `mock_aws` y crea las 5 tablas del backend via el ORM.

    Usa `BaseModel.create_table()` para ejercitar tambien la ruta DDL.
    """
    from shared.dynamodb import (
        CacheItem,
        ContactItem,
        RateLimitBucketItem,
        RateLimitRuleItem,
        TrackingEventItem,
    )

    with mock_aws():
        reset_resource_cache()
        for model in (
            ContactItem,
            TrackingEventItem,
            CacheItem,
            RateLimitBucketItem,
            RateLimitRuleItem,
        ):
            model.create_table()
        yield
        reset_resource_cache()


@pytest.fixture
def mock_aws_no_tables() -> Generator[None]:
    """Levanta `mock_aws` SIN crear ninguna tabla.

    Para tests que crean tablas a mano (ej. drift de esquema) o esperan
    la ausencia de la tabla.
    """
    with mock_aws():
        reset_resource_cache()
        yield
        reset_resource_cache()


@pytest.fixture
def ses_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[str]:
    """Levanta `mock_aws` con una identidad SES verificada.

    `shared.aws.ses` crea su cliente `ses` a module-scope (al importar):
    si ese import ocurrio fuera de un `mock_aws()`, el cliente apunta a
    AWS real. Por eso la fixture recrea el cliente DENTRO del mock y lo
    rebindea en el modulo via monkeypatch.

    Cede la from-address verificada que los tests usan como remitente.
    """
    from_address = 'no-reply@the-full-stack.com'
    with mock_aws():
        # SES v1 verifica la identidad; sesv2 (que usa shared.aws.ses)
        # comparte el mismo backend moto.
        ses_v1 = boto3.client('ses', region_name='us-east-1')
        ses_v1.verify_domain_identity(Domain='the-full-stack.com')
        ses_v1.verify_email_identity(EmailAddress=from_address)
        # Rebindear el cliente module-scope al que moto intercepta.
        # `import shared.aws.ses` puede resolver al objeto re-exportado;
        # `importlib.import_module` garantiza el modulo.
        import importlib

        ses_module = importlib.import_module('shared.aws.ses')
        monkeypatch.setattr(
            ses_module,
            'ses',
            boto3.client('sesv2', region_name='us-east-1'),
        )
        yield from_address


class _SSMHandle:
    """Handle de la fixture `ssm_with_kms`: cliente SSM + KMS key id."""

    def __init__(self, client: object, kms_key_id: str) -> None:
        self.client = client
        self.kms_key_id = kms_key_id


@pytest.fixture
def ssm_with_kms() -> Generator[_SSMHandle]:
    """Levanta `mock_aws` con una KMS key + cliente SSM listo.

    Cede un `_SSMHandle` con el cliente boto3 SSM (para crear los
    `SecureString`) y el id de la KMS key (para cifrarlos).
    """
    from shared.aws.ssm import clear_cache

    with mock_aws():
        clear_cache()
        kms = boto3.client('kms', region_name='us-east-1')
        key = kms.create_key(Description='portfolio integration tests')
        key_id = key['KeyMetadata']['KeyId']
        ssm = boto3.client('ssm', region_name='us-east-1')
        yield _SSMHandle(ssm, key_id)
        clear_cache()
