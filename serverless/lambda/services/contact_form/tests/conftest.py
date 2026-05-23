"""Configuracion pytest del Lambda `contact_form`.

Agrega `core/` al `sys.path` para que los imports absolutos del codigo
(`handler`, `controllers.`, `services.`, `models.`, `settings.`,
`utils.`) resuelvan en los tests.

La libreria comun `shared/` normalmente se vendoriza en `core/shared/`
por devtools antes de correr los tests (`serverless test-unit` lo hace).
Si no esta vendorizada (pytest invocado directo), este conftest agrega
`serverless/` al path como fallback para que `import shared...` resuelva
desde la fuente maestra `serverless/lambda/shared/`.

Setea las env vars minimas que `AppConfig` (settings/config.py) y el
codigo del Lambda necesitan, y expone el fixture `contact_form_aws` que
monta el entorno AWS mockeado (DynamoDB + SSM + SES) con moto.
"""

import os
import sys
from collections.abc import Generator
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

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

# Env vars minimas para que AppConfig cargue sin un entorno Lambda real.
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('AWS_SES_REGION', 'us-east-1')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'contact-form-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')


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
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')


@pytest.fixture
def contact_form_aws(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None]:
    """Monta el entorno AWS mockeado del Lambda contact_form.

    Crea con moto las cuatro tablas DynamoDB (contacts, cache,
    rate-limit-rules, rate-limit-buckets), los tres parametros SSM
    (turnstile-secret, owner-email, ses-from-address) y la identidad SES
    `the-full-stack.com`. Setea las env vars que apuntan a esos recursos.
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
    monkeypatch.setenv(
        'SSM_SES_FROM_ADDRESS_PATH', '/portfolio-test/ses-from-address'
    )
    monkeypatch.setenv(
        'CORS_ALLOWED_ORIGINS',
        'https://the-full-stack.com,'
        'https://www.the-full-stack.com,'
        'https://hub.portfolio.the-full-stack.com,'
        'https://fintech.portfolio.the-full-stack.com,'
        'https://architect.portfolio.the-full-stack.com,'
        'https://leader.portfolio.the-full-stack.com,'
        'https://vibe.portfolio.the-full-stack.com',
    )

    with mock_aws():
        # El resource DynamoDB singleton de shared.aws.dynamodb se
        # recrea bajo este mock_aws() para aislar el estado entre tests.
        from shared.aws.dynamodb import reset_resource_cache

        reset_resource_cache()

        ddb = boto3.client('dynamodb', region_name='us-east-1')
        ddb.create_table(
            TableName='portfolio-contacts-test',
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
            ],
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
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
            KeySchema=[
                {'AttributeName': 'bucket_key', 'KeyType': 'HASH'},
            ],
            BillingMode='PAY_PER_REQUEST',
        )

        ssm = boto3.client('ssm', region_name='us-east-1')
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

        ses = boto3.client('sesv2', region_name='us-east-1')
        ses.create_email_identity(EmailIdentity='the-full-stack.com')
        ses.create_email_identity(
            EmailIdentity='no-reply@the-full-stack.com'
        )

        yield
