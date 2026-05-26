"""
Given un batch SQS de 10 records validos,
When lambda_handler procesa,
Then retorna {batchItemFailures: []} (todos los mensajes exitosos) y
     una sola db_session se uso para los 10.

AC-12 / AC-13 (camino feliz).
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import lambda_context, sqs_batch, sqs_record


@pytest.mark.unit
def test_handler_processes_full_batch_no_failures(
    db_session_calls: list[int],
    session_visit_calls: list[dict],
    insert_tracking_calls: list[dict],
    patch_parse_user_agent: None,
) -> None:
    # Arrange
    _ = patch_parse_user_agent
    from handler import lambda_handler

    event = sqs_batch([sqs_record(index=i) for i in range(10)])

    # Act
    result = lambda_handler(event, lambda_context())

    # Assert
    assert result == {'batchItemFailures': []}
    assert len(db_session_calls) == 1
    assert len(session_visit_calls) == 10
    assert len(insert_tracking_calls) == 10
