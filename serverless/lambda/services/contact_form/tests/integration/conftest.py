"""Configuracion pytest de los integration tests del Lambda `contact_form`.

Los integration tests ejercitan el flujo end-to-end del Lambda: invocan
el `lambda_handler` real con un evento API Gateway crudo y verifican el
efecto observable completo (respuesta HTTP + estado en DynamoDB + email
enviado por SES). NO se mockea codigo propio (handler, controller,
service, models): la unica frontera mockeada es AWS (DynamoDB, SES, SSM
via moto) y la llamada HTTP a Cloudflare Turnstile (via respx).

A diferencia del `conftest.py` raiz del Lambda — que mockea el entorno
para los unit tests — este conftest:

  - Monta moto COMPLETO (DynamoDB con las 4 tablas + SSM + SES) y deja el
    codigo de negocio intacto.
  - Aisla el estado entre tests: cada test recibe un entorno AWS limpio
    via la fixture autouse `aws_env`.
  - Limpia el cache de SSM (Powertools) y el resource boto3 singleton de
    DynamoDB antes de cada test, para que el estado no se filtre entre
    tests.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

# core/ al path: imports absolutos del codigo del Lambda (handler,
# controllers., services., models., settings., utils.).
_LAMBDA_ROOT = Path(__file__).resolve().parents[2]
_CORE = _LAMBDA_ROOT / 'core'
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

# Fallback para `import shared...` si no esta vendorizado en core/shared/.
# La fuente maestra shared/ vive en serverless/lambda/.
if not (_CORE / 'shared').is_dir():
    _LAMBDA_BASE = _LAMBDA_ROOT.parents[1]
    if str(_LAMBDA_BASE) not in sys.path:
        sys.path.insert(0, str(_LAMBDA_BASE))

# Env vars minimas para que AppConfig cargue sin un entorno Lambda real.
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('AWS_SES_REGION', 'us-east-1')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'contact-form-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')

_REGION = 'us-east-1'
_CORS_ORIGINS = (
    'https://the-full-stack.com,'
    'https://www.the-full-stack.com,'
    'https://hub.portfolio.the-full-stack.com,'
    'https://fintech.portfolio.the-full-stack.com,'
    'https://architect.portfolio.the-full-stack.com,'
    'https://leader.portfolio.the-full-stack.com,'
    'https://vibe.portfolio.the-full-stack.com'
)


@pytest.fixture(autouse=True)
def _aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setea credenciales AWS fake (autouse).

    Previene que boto3 lea ~/.aws/credentials reales o intente STS. Es
    necesario para que moto intercepte las llamadas.
    """
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', _REGION)
    monkeypatch.setenv('AWS_REGION', _REGION)


def _create_tables(ddb: object) -> None:
    """Crea las 4 tablas DynamoDB que el Lambda contact_form usa."""
    ddb.create_table(  # type: ignore[attr-defined]
        TableName='portfolio-contacts-test',
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        BillingMode='PAY_PER_REQUEST',
    )
    ddb.create_table(  # type: ignore[attr-defined]
        TableName='portfolio-cache-test',
        AttributeDefinitions=[
            {'AttributeName': 'cache_key', 'AttributeType': 'S'},
        ],
        KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
        BillingMode='PAY_PER_REQUEST',
    )
    ddb.create_table(  # type: ignore[attr-defined]
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
    ddb.create_table(  # type: ignore[attr-defined]
        TableName='portfolio-rate-limit-buckets-test',
        AttributeDefinitions=[
            {'AttributeName': 'bucket_key', 'AttributeType': 'S'},
        ],
        KeySchema=[{'AttributeName': 'bucket_key', 'KeyType': 'HASH'}],
        BillingMode='PAY_PER_REQUEST',
    )


@pytest.fixture
def aws_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Monta el entorno AWS mockeado end-to-end del Lambda contact_form.

    Crea con moto las 4 tablas DynamoDB (contacts, cache,
    rate-limit-rules, rate-limit-buckets), los 3 parametros SSM
    (turnstile-secret, owner-email, ses-from-address) y verifica las
    identidades SES. Setea las env vars que apuntan a esos recursos y
    aisla el estado entre tests (resource singleton + cache SSM).
    """
    monkeypatch.setenv('CONTACTS_TABLE_NAME', 'portfolio-contacts-test')
    monkeypatch.setenv('CACHE_TABLE_NAME', 'portfolio-cache-test')
    monkeypatch.setenv(
        'RATE_LIMIT_RULES_TABLE_NAME', 'portfolio-rate-limit-rules-test'
    )
    monkeypatch.setenv(
        'RATE_LIMIT_BUCKETS_TABLE_NAME', 'portfolio-rate-limit-buckets-test'
    )
    monkeypatch.setenv(
        'SSM_TURNSTILE_SECRET_PATH', '/portfolio-test/turnstile-secret'
    )
    monkeypatch.setenv('SSM_OWNER_EMAIL_PATH', '/portfolio-test/owner-email')
    monkeypatch.setenv('SSM_SES_FROM_PATH', '/portfolio-test/ses-from-address')
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', _CORS_ORIGINS)

    with mock_aws():
        # Aislar el resource DynamoDB singleton y el cache SSM Powertools
        # bajo este mock_aws(): asi el estado no se filtra entre tests.
        from shared.aws.dynamodb import reset_resource_cache
        from shared.aws.ssm import clear_cache as clear_ssm_cache

        reset_resource_cache()
        clear_ssm_cache()

        ddb = boto3.client('dynamodb', region_name=_REGION)
        _create_tables(ddb)

        ssm = boto3.client('ssm', region_name=_REGION)
        ssm.put_parameter(
            Name='/portfolio-test/turnstile-secret',
            Value='test-turnstile-secret',
            Type='SecureString',
        )
        ssm.put_parameter(
            Name='/portfolio-test/owner-email',
            Value='owner@example.com',
            Type='String',
        )
        ssm.put_parameter(
            Name='/portfolio-test/ses-from-address',
            Value='no-reply@the-full-stack.com',
            Type='String',
        )

        ses = boto3.client('sesv2', region_name=_REGION)
        ses.create_email_identity(EmailIdentity='the-full-stack.com')
        ses.create_email_identity(
            EmailIdentity='no-reply@the-full-stack.com'
        )

        yield

        # Cleanup: descartar el resource singleton y el cache SSM para que
        # el proximo test no vea estado del mock ya cerrado.
        reset_resource_cache()
        clear_ssm_cache()
