"""Test: si la persistencia levanta, el handler marca batchItemFailure.

Given un batch SQS con 1 mensaje valido, y save_contact_idempotent
levanta una excepcion (ej. Neon caido o connection reset),
When lambda_handler procesa el batch,
Then el record va en batchItemFailures con su messageId para que SQS lo
     reintente (hasta max_receive_count=3 antes de DLQ).

AC-11: la robustez del worker — si la persistencia falla, el mensaje
NO se pierde silenciosamente.
"""

import pytest

from tests.unit._helpers import lambda_context, sqs_event

pytestmark = pytest.mark.unit


def test_handler_marks_failed_items_when_persistence_throws(monkeypatch):
    # Arrange: la persistencia levanta
    from controllers.worker import process as process_module
    from handler import lambda_handler

    def _raise_neon_error(_msg):
        raise RuntimeError('Neon connection refused')

    monkeypatch.setattr(
        process_module,
        'save_contact_idempotent',
        _raise_neon_error,
    )
    # send_owner_email_safe no debe llegar a llamarse; lo seteamos a un
    # stub para que un bug en el flujo se note (lista vacia esperada).
    email_calls: list = []
    monkeypatch.setattr(
        process_module,
        'send_owner_email_safe',
        lambda msg, persist_result: email_calls.append(msg) or 'ok',
    )

    event = sqs_event()
    ctx = lambda_context()

    # Act
    result = lambda_handler(event, ctx)

    # Assert: el unico record fallido va en batchItemFailures
    assert result == {
        'batchItemFailures': [
            {'itemIdentifier': '019e5c50-0000-7000-8000-msg00000001'},
        ],
    }
    # Assert: el email NO se intento (la persistencia fallo antes)
    assert email_calls == []
