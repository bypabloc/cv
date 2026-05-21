"""Fixtures para tests contact_form."""

from __future__ import annotations

from collections.abc import Generator

import boto3
import pytest
from moto import mock_aws

from shared.dynamodb_client import reset_resource_cache


@pytest.fixture
def contact_form_aws(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """
    Setup AWS mock con todas las tablas + SSM Parameters + SES domain identity.

    Tablas: contacts, cache, rate-limit-rules, rate-limit-buckets.
    SSM Parameters: turnstile-secret, owner-email, ses-from-address.
    SES: the-full-stack.com domain identity verificada.
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
    monkeypatch.setenv(
        'SSM_OWNER_EMAIL_PATH', '/portfolio-test/owner-email'
    )
    monkeypatch.setenv(
        'SSM_SES_FROM_PATH', '/portfolio-test/ses-from-address'
    )
    monkeypatch.setenv('POWERTOOLS_SERVICE_NAME', 'contact-form-test')
    monkeypatch.setenv('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')
    # Whitelist CORS/Turnstile (en runtime la inyecta Mappings.StageConfig).
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
        # El resource DynamoDB singleton se recrea bajo este mock_aws().
        reset_resource_cache()
        # DynamoDB tables
        ddb = boto3.client('dynamodb', region_name='us-east-1')
        ddb.create_table(
            TableName='portfolio-contacts-test',
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
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
            KeySchema=[{'AttributeName': 'bucket_key', 'KeyType': 'HASH'}],
            BillingMode='PAY_PER_REQUEST',
        )

        # SSM Parameters
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

        # SES domain identity (moto)
        ses = boto3.client('sesv2', region_name='us-east-1')
        ses.create_email_identity(EmailIdentity='the-full-stack.com')
        ses.create_email_identity(EmailIdentity='no-reply@the-full-stack.com')

        yield
