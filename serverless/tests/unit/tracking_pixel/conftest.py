"""Fixtures para tests tracking_pixel."""

from __future__ import annotations

from collections.abc import Generator

import boto3
import pytest
from moto import mock_aws

from _shared.dynamodb_client import reset_resource_cache


@pytest.fixture
def tracking_aws(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Setup AWS mock con tracking/cache/rate-limit tables."""
    monkeypatch.setenv('TRACKING_TABLE_NAME', 'portfolio-tracking-test')
    monkeypatch.setenv('CACHE_TABLE_NAME', 'portfolio-cache-test')
    monkeypatch.setenv(
        'RATE_LIMIT_RULES_TABLE_NAME', 'portfolio-rate-limit-rules-test'
    )
    monkeypatch.setenv(
        'RATE_LIMIT_BUCKETS_TABLE_NAME', 'portfolio-rate-limit-buckets-test'
    )

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
