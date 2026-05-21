"""Fixtures para los tests del ORM DynamoDB.

`dynamodb_tables` levanta un `mock_aws` y crea las 5 tablas del backend
USANDO el propio ORM (`BaseModel.create_table`). Asi los tests del ORM
ejercitan tambien la ruta DDL de creacion. `dynamodb_env` apunta las env
vars de cada modelo a los nombres `*-test`.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from moto import mock_aws

from shared.dynamodb import (
    CacheItem,
    ContactItem,
    RateLimitBucketItem,
    RateLimitRuleItem,
    TrackingEventItem,
)
from shared.dynamodb_client import reset_resource_cache

_ALL_MODELS = (
    ContactItem,
    TrackingEventItem,
    CacheItem,
    RateLimitBucketItem,
    RateLimitRuleItem,
)


@pytest.fixture(autouse=True)
def dynamodb_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Apunta cada modelo a su tabla `*-test` (autouse)."""
    monkeypatch.setenv('CONTACTS_TABLE_NAME', 'portfolio-contacts-test')
    monkeypatch.setenv('TRACKING_TABLE_NAME', 'portfolio-tracking-test')
    monkeypatch.setenv('CACHE_TABLE_NAME', 'portfolio-cache-test')
    monkeypatch.setenv(
        'RATE_LIMIT_RULES_TABLE_NAME', 'portfolio-rate-limit-rules-test'
    )
    monkeypatch.setenv(
        'RATE_LIMIT_BUCKETS_TABLE_NAME',
        'portfolio-rate-limit-buckets-test',
    )


@pytest.fixture
def dynamodb_tables() -> Generator[None]:
    """Levanta `mock_aws` y crea las 5 tablas via el ORM."""
    with mock_aws():
        # El resource singleton se recrea bajo este mock_aws().
        reset_resource_cache()
        for model in _ALL_MODELS:
            model.create_table()
        yield
        reset_resource_cache()


@pytest.fixture
def mock_aws_no_tables() -> Generator[None]:
    """Levanta `mock_aws` SIN crear tablas (para tests de tabla ausente)."""
    with mock_aws():
        reset_resource_cache()
        yield
        reset_resource_cache()
