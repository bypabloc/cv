"""
Given _build_client falla con BotoCoreError para dynamodb pero ok para sqs y ssm,
When register_warmup(['sqs', 'dynamodb', 'ssm']) corre,
Then loguea WARNING para dynamodb, completa sin raise.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import BotoCoreError

pytestmark = pytest.mark.unit


def test_register_warmup_continues_when_one_client_fails(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Un build falla NO aborta el resto ni propaga la excepcion."""
    # Arrange: build_client devuelve un mock para sqs/ssm, raise para dynamodb
    def build_client_factory(service: str, _region: str) -> MagicMock:
        if service == 'dynamodb':
            raise BotoCoreError
        return MagicMock()

    # Act
    with patch(
        'shared.lambda_kit.snap_start_warmup._build_client',
        side_effect=build_client_factory,
    ), caplog.at_level(logging.WARNING, logger='snap_start_warmup'):
        from shared.lambda_kit.snap_start_warmup import register_warmup

        # NO debe raise
        register_warmup(['sqs', 'dynamodb', 'ssm'])

    # Assert
    warnings = [r for r in caplog.records if r.levelname == 'WARNING']
    assert len(warnings) == 1
    assert 'dynamodb' in warnings[0].message
    assert 'failed' in warnings[0].message
