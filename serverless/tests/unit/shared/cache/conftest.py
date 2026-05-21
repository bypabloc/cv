"""Fixtures locales para tests de cache."""

from __future__ import annotations

from collections.abc import Generator

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def cache_table() -> Generator[str]:
    """
    Crea la tabla portfolio-cache-test en moto y retorna el nombre.

    Mismo schema que en SAM template SPEC-001.
    """
    with mock_aws():
        client = boto3.client('dynamodb', region_name='us-east-1')
        table_name = 'portfolio-cache-test'
        client.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {'AttributeName': 'cache_key', 'AttributeType': 'S'},
            ],
            KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
            BillingMode='PAY_PER_REQUEST',
        )
        client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'expires_at',
            },
        )
        yield table_name


@pytest.fixture(autouse=True)
def cache_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setea CACHE_TABLE_NAME para que DynamoDBCache() lo lea."""
    monkeypatch.setenv('CACHE_TABLE_NAME', 'portfolio-cache-test')
