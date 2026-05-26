"""
Given dynamodb falla con BotoCoreError pero sqs y ssm exito,
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
    """Un client fallando NO aborta el resto ni propaga la excepcion."""
    # Arrange: build_client devuelve un mock distinto por servicio.
    def build_client_factory(service: str, _region: str) -> MagicMock:
        c = MagicMock()
        if service == 'dynamodb':
            c.describe_endpoints.side_effect = BotoCoreError()
        else:
            c.list_queues.return_value = {'QueueUrls': []}
            c.describe_parameters.return_value = {'Parameters': []}
        return c

    # Act
    with patch(
        'shared.lambda_kit.snap_start_warmup._build_client',
        side_effect=build_client_factory,
    ):
        with caplog.at_level(logging.WARNING, logger='snap_start_warmup'):
            from shared.lambda_kit.snap_start_warmup import register_warmup

            # NO debe raise
            register_warmup(['sqs', 'dynamodb', 'ssm'])

    # Assert
    warnings = [r for r in caplog.records if r.levelname == 'WARNING']
    assert len(warnings) == 1
    assert 'dynamodb' in warnings[0].message
    assert 'failed' in warnings[0].message
