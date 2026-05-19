"""Fixtures para tests del modulo _shared."""

from __future__ import annotations

from collections.abc import Generator

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def turnstile_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """
    Setup minimo para tests de _shared.turnstile.

    Solo SSM (turnstile-secret) + las env vars que verify_turnstile_token
    consulta: SSM_TURNSTILE_SECRET_PATH y CORS_ALLOWED_ORIGINS (whitelist de
    hostnames). NO crea tablas DynamoDB ni SES — el modulo no las toca.
    En runtime CORS_ALLOWED_ORIGINS la inyecta Mappings.StageConfig.
    """
    monkeypatch.setenv(
        'SSM_TURNSTILE_SECRET_PATH', '/portfolio-test/turnstile-secret'
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
        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/portfolio-test/turnstile-secret',
            Value='test-turnstile-secret',
            Type='SecureString',
        )
        yield
