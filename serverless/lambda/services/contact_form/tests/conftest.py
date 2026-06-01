"""Configuracion pytest del Lambda `contact_form`.

Agrega `core/` al `sys.path` para que los imports absolutos del codigo
(`handler`, `controllers.`, `services.`, `models.`, `settings.`,
`utils.`) resuelvan en los tests.

La libreria comun `shared/` normalmente se vendoriza en `core/shared/`
por devtools antes de correr los tests (`serverless test-unit` lo hace).
Si no esta vendorizada (pytest invocado directo), este conftest agrega
`serverless/` al path como fallback para que `import shared...` resuelva
desde la fuente maestra `serverless/lambda/shared/`.

Setea las env vars minimas que el codigo del Lambda necesita, y expone
el fixture `contact_form_aws` que monta el entorno AWS mockeado (DynamoDB
+ SSM) con moto. El email al owner se delega a `send_email` via invoke
async; los tests lo capturan con el fixture `mock_invoke`.
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
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'contact-form-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')
# Nombre del Lambda send_email que el service invoca async (lo inyecta
# devtools en runtime desde uses.invokes; aqui un valor determinista).
os.environ.setdefault(
    'LAMBDA_SEND_EMAIL_FUNCTION_NAME', 'portfolio-send-email-test'
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
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')


@pytest.fixture
def contact_form_aws(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None]:
    """Monta el entorno AWS mockeado del Lambda contact_form.

    Crea con moto las tablas DynamoDB (cache, rate-limit-rules,
    rate-limit-buckets) y los parametros SSM (turnstile-secret,
    owner-email).

    Setea las env vars que apuntan a esos recursos. El email al owner se
    delega a `send_email` via invoke async (sin SQS, sin SES directo); los
    tests lo capturan con el fixture `mock_invoke`.
    """
    # CONTACTS_TABLE_NAME se elimino (spec direct-neon-writes): el Lambda
    # ya no escribe a DynamoDB.contacts. La connection string de Neon va
    # por DATABASE_URL/DB_URL que mockeamos por test (no hace falta default
    # aqui — los tests que persisten usan mock_neon_writes).
    monkeypatch.setenv('DATABASE_URL', 'postgresql://test:test@localhost/test')
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
        # La tabla `contacts` se elimino (spec direct-neon-writes): el
        # Lambda escribe directo a Neon. Los tests de persistencia usan
        # el fixture `mock_neon_writes`.
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

        # shared.aws.ssm cachea el SSM resolver. Limpiar la cache para que
        # el fixture aisle el estado entre tests.
        import shared.aws.ssm as _ssm_mod

        if hasattr(_ssm_mod, 'get_secret') and hasattr(
            _ssm_mod.get_secret,
            'cache_clear',
        ):
            _ssm_mod.get_secret.cache_clear()

        yield


@pytest.fixture
def mock_invoke(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Captura los invokes async a `send_email` via `invoke_async`.

    Mockea `services.contact_service.invoke_async` para evitar tocar
    Lambda en los tests unit. El test inspecciona el payload exacto que
    el service arma para `send_email` (kind=contact).

    Returns
    -------
    list[dict]
        Lista de `{function_name, payload}` que el service invoco. El
        test asserta len(captured) y el shape del primero.
    """
    captured: list[dict] = []

    def _fake_invoke(*, function_name: str, payload: dict) -> str:
        captured.append({'function_name': function_name, 'payload': payload})
        return 'fake-invoke-request-id'

    monkeypatch.setattr(
        'services.contact_service.invoke_async',
        _fake_invoke,
    )
    return captured


_STUB_VISIT_ID = '019e5c50-0000-7000-8000-000000000002'
"""visit_id determinista (UUIDv7 valido) que el mock de
`ensure_session_and_visit` retorna en los tests de contact_form."""


@pytest.fixture
def session_visit_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Captura los kwargs de cada invocacion a `ensure_session_and_visit`.

    Retorna un visit_id determinista. Mockea el helper en
    `services.contact_service`. Spec sessions-normalize: el contact
    UPSERTea session + visit via este helper antes del INSERT del row.
    """
    captured: list[dict] = []

    def _fake_ensure(_session: object, **kwargs: object) -> tuple[str, str]:
        captured.append(dict(kwargs))
        return str(kwargs['session_id']), _STUB_VISIT_ID

    monkeypatch.setattr(
        'services.contact_service.ensure_session_and_visit', _fake_ensure
    )
    return captured


@pytest.fixture
def mock_neon_writes(
    monkeypatch: pytest.MonkeyPatch,
    session_visit_calls: list[dict],
) -> list[dict]:
    """Mockea `db_session()` + `ensure_session_and_visit` + `insert_contact()`.

    Captura los payloads de `insert_contact`. Para inspeccionar los args
    del helper, agregar `session_visit_calls` como fixture explicito.

    Spec sessions-normalize: el service UPSERTea session + visit antes
    del INSERT del contact en la misma tx. En unit tests no levantamos
    un Postgres real: mockeamos las 3 escrituras.
    """
    from contextlib import contextmanager

    # session_visit_calls inyectado para que el helper se mockee.
    _ = session_visit_calls

    captured: list[dict] = []

    @contextmanager
    def _fake_db_session():
        yield object()

    def _fake_insert_contact(_session: object, payload: dict) -> None:
        captured.append(payload)

    monkeypatch.setattr('services.contact_service.db_session', _fake_db_session)
    monkeypatch.setattr(
        'services.contact_service.insert_contact', _fake_insert_contact
    )
    return captured
