"""Fixtures de shared.queue tests."""

import sys
from pathlib import Path

import pytest

# Agregar serverless/lambda/ al path para imports `shared.queue.*` y
# `shared.aws.*` durante los tests aislados del subpaquete.
_SHARED_ROOT = Path(__file__).resolve().parents[3]
if str(_SHARED_ROOT) not in sys.path:
    sys.path.insert(0, str(_SHARED_ROOT))


@pytest.fixture(autouse=True)
def _aws_env(monkeypatch):
    """AWS testing env vars (para boto3/moto)."""
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')


@pytest.fixture(autouse=True)
def _clear_caches():
    """Limpia los lru_cache entre tests para aislar el estado."""
    from shared.queue.client import get_sqs_client
    get_sqs_client.cache_clear()
    yield
    get_sqs_client.cache_clear()
