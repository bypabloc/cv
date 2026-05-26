"""
Given un batch SQS de 3 records, el segundo causa una excepcion en
     `process_tracking_message` (simula FK violation no esperada),
When lambda_handler procesa,
Then los records 1 y 3 procesan exitosamente; el 2 va en
     batchItemFailures con su messageId.

AC-13: fallo individual de un mensaje no aborta el batch entero.
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import lambda_context, sqs_batch, sqs_record


@pytest.mark.unit
def test_handler_continues_after_single_item_exception(
    db_session_calls: list[int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    _ = db_session_calls
    from handler import lambda_handler

    processed: list[str] = []

    # Stub: process_tracking_message corre el INSERT excepto si es el
    # segundo (page_id termina en ...0000000001). Asi el segundo
    # mensaje va a failures con su messageId; los otros 2 procesan ok.
    def _fake_process(_session: object, msg: object) -> bool:
        page_id = msg.page_id
        processed.append(page_id)
        if page_id.endswith('000000000001'):
            raise RuntimeError('simulated FK violation')
        return True

    monkeypatch.setattr(
        'controllers.worker.process_batch.process_tracking_message',
        _fake_process,
    )

    record0 = sqs_record(index=0)
    record1 = sqs_record(index=1)  # el que falla
    record2 = sqs_record(index=2)
    event = sqs_batch([record0, record1, record2])

    # Act
    result = lambda_handler(event, lambda_context())

    # Assert: solo el record1 reporta failure, con su messageId
    # original.
    assert result == {
        'batchItemFailures': [
            {'itemIdentifier': record1['messageId']},
        ],
    }
    # Los 3 mensajes fueron procesados (el 1 lanzo, los otros 2
    # completaron). Esto valida que el loop NO aborto tras la
    # excepcion del segundo.
    assert len(processed) == 3
