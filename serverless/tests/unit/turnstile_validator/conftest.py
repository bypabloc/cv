"""Fixtures para turnstile_validator tests."""

from __future__ import annotations

from collections.abc import Generator

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def turnstile_aws(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
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

    with mock_aws():
        ddb = boto3.client('dynamodb', region_name='us-east-1')
        for table_name, keys in [
            ('portfolio-cache-test', [('cache_key', 'HASH')]),
            (
                'portfolio-rate-limit-rules-test',
                [('rule_key', 'HASH'), ('kind', 'RANGE')],
            ),
            (
                'portfolio-rate-limit-buckets-test',
                [('bucket_key', 'HASH')],
            ),
        ]:
            ddb.create_table(
                TableName=table_name,
                AttributeDefinitions=[
                    {'AttributeName': k[0], 'AttributeType': 'S'} for k in keys
                ],
                KeySchema=[
                    {'AttributeName': k[0], 'KeyType': k[1]} for k in keys
                ],
                BillingMode='PAY_PER_REQUEST',
            )

        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/portfolio-test/turnstile-secret',
            Value='test-secret',
            Type='SecureString',
        )
        yield
