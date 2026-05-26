"""
Given los 3 clientes (sqs, dynamodb, ssm) se instancian sin error,
When register_warmup(['sqs', 'dynamodb', 'ssm']) corre,
Then loguea 3 lineas INFO con prefijo [snap_start_warmup] X: ok (Yms).
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


def test_register_warmup_logs_ok_when_all_clients_succeed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Las 3 instanciaciones exitosas producen 3 lineas INFO 'ok'."""
    # Arrange: build_client retorna un mock cualquiera (no se llama nada)
    mock_client = MagicMock()

    # Act
    with patch(
        'shared.lambda_kit.snap_start_warmup._build_client',
        return_value=mock_client,
    ), caplog.at_level(logging.INFO, logger='snap_start_warmup'):
        from shared.lambda_kit.snap_start_warmup import register_warmup

        register_warmup(['sqs', 'dynamodb', 'ssm'])

    # Assert
    ok_logs = [r for r in caplog.records if 'ok' in r.message]
    assert len(ok_logs) == 3
    assert any('sqs: ok' in r.message for r in ok_logs)
    assert any('dynamodb: ok' in r.message for r in ok_logs)
    assert any('ssm: ok' in r.message for r in ok_logs)
