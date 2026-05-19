"""
Fixtures globales para tests del backend serverless.

Convenciones:
- Fixtures de moto van en `moto_*` para distinguir de fixtures locales.
- `aws_credentials` fixture es obligatoria antes de cualquier mock_aws
  para que boto3 no intente STS real.
- `monkeypatch_settings` resetea el singleton de config en cada test.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# Permitir imports de `_shared.*` directamente (src/ esta en path)
_SRC = Path(__file__).parent.parent / 'src'
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Setea AWS credentials fake en todos los tests (autouse).

    Previene que boto3 lea ~/.aws/credentials reales o intente STS.
    Necesario para que moto interceptee las llamadas.
    """
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    monkeypatch.setenv('POWERTOOLS_SERVICE_NAME', 'test-service')
    monkeypatch.setenv('POWERTOOLS_METRICS_NAMESPACE', 'TestNamespace')


@pytest.fixture(autouse=True, scope='session')
def _setup_powertools_env() -> None:
    """
    Setea env vars de Powertools ANTES del import de _shared.metrics.

    pytest carga conftest antes que cualquier test module. Pero _shared.metrics
    se importa solo cuando un test hace `from _shared.metrics import metrics`,
    asi que setear los env aqui (al import del conftest) es suficiente.
    """
    os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'test-service')
    os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'TestNamespace')


@pytest.fixture(autouse=True)
def reset_settings_cache() -> Generator[None]:
    """Resetea el singleton de Settings entre tests (autouse)."""
    yield
    # Limpiar cache al final del test (no al inicio: otros fixtures pueden
    # haber seteado env vars que el test quiere ver).
    try:
        from _shared.config import get_settings
        get_settings.cache_clear()
    except ImportError:
        pass


@pytest.fixture
def default_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setea env vars default para tests que necesitan settings poblados."""
    monkeypatch.setenv('STAGE', 'dev')
    monkeypatch.setenv('LOG_LEVEL', 'INFO')
    monkeypatch.setenv('CONTACTS_TABLE_NAME', 'portfolio-contacts-dev')
    monkeypatch.setenv('TRACKING_TABLE_NAME', 'portfolio-tracking-dev')
    monkeypatch.setenv('CACHE_TABLE_NAME', 'portfolio-cache-dev')
    monkeypatch.setenv('SSM_TURNSTILE_SECRET_PATH', '/portfolio/turnstile-secret')


@pytest.fixture
def api_gw_event() -> dict:
    """Event factory: API GW REST proxy con shape estandar."""

    def _factory(
        *,
        method: str = 'POST',
        path: str = '/contact',
        headers: dict[str, str] | None = None,
        body: str | None = None,
        source_ip: str = '1.2.3.4',
    ) -> dict:
        return {
            'httpMethod': method,
            'path': path,
            'headers': headers or {'Content-Type': 'application/json'},
            'queryStringParameters': None,
            'pathParameters': None,
            'body': body,
            'isBase64Encoded': False,
            'requestContext': {
                'identity': {'sourceIp': source_ip},
                'requestId': 'test-request-id',
                'stage': 'dev',
            },
        }

    return _factory
