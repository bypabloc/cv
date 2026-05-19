"""Fixtures locales para tests rate_limit."""

from __future__ import annotations

from collections.abc import Generator

import boto3
import pytest
from moto import mock_aws

from _shared.dynamodb_client import reset_resource_cache


@pytest.fixture
def rate_limit_tables() -> Generator[dict[str, str]]:
    """
    Crea las 3 tablas necesarias para tests de rate-limit:
    - portfolio-cache-test (para @cached en rules.py)
    - portfolio-rate-limit-rules-test
    - portfolio-rate-limit-buckets-test
    """
    with mock_aws():
        # El resource DynamoDB singleton se recrea bajo este mock_aws().
        reset_resource_cache()
        client = boto3.client('dynamodb', region_name='us-east-1')

        # Cache table
        client.create_table(
            TableName='portfolio-cache-test',
            AttributeDefinitions=[
                {'AttributeName': 'cache_key', 'AttributeType': 'S'},
            ],
            KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
            BillingMode='PAY_PER_REQUEST',
        )
        client.update_time_to_live(
            TableName='portfolio-cache-test',
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'expires_at',
            },
        )

        # Rules table (composite PK + SK)
        client.create_table(
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
        client.update_time_to_live(
            TableName='portfolio-rate-limit-rules-test',
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'expires_at',
            },
        )

        # Buckets table (PK only)
        client.create_table(
            TableName='portfolio-rate-limit-buckets-test',
            AttributeDefinitions=[
                {'AttributeName': 'bucket_key', 'AttributeType': 'S'},
            ],
            KeySchema=[{'AttributeName': 'bucket_key', 'KeyType': 'HASH'}],
            BillingMode='PAY_PER_REQUEST',
        )
        client.update_time_to_live(
            TableName='portfolio-rate-limit-buckets-test',
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'expires_at',
            },
        )

        yield {
            'cache': 'portfolio-cache-test',
            'rules': 'portfolio-rate-limit-rules-test',
            'buckets': 'portfolio-rate-limit-buckets-test',
        }


@pytest.fixture(autouse=True)
def rate_limit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setea env vars para que el modulo apunte a las tablas test."""
    monkeypatch.setenv('CACHE_TABLE_NAME', 'portfolio-cache-test')
    monkeypatch.setenv(
        'RATE_LIMIT_RULES_TABLE_NAME', 'portfolio-rate-limit-rules-test'
    )
    monkeypatch.setenv(
        'RATE_LIMIT_BUCKETS_TABLE_NAME', 'portfolio-rate-limit-buckets-test'
    )
