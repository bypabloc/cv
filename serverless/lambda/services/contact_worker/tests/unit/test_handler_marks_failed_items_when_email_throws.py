"""Test: si SES falla, el handler marca batchItemFailure.

Given un batch SQS con 1 mensaje valido, persistencia OK y
send_owner_email_safe levanta una excepcion (ej. SES throttle, identidad
no verificada, ConnectTimeout),
When lambda_handler procesa el batch,
Then el record va en batchItemFailures con su messageId para que SQS lo
     reintente.

AC-11: a diferencia del flujo sync legacy (que silenciaba el error y
contaba metrica OwnerEmailFailed), el worker propaga el fallo. Como
save_contact_idempotent es no-op en reintentos, el owner puede recibir
el mismo email max 3 veces antes del DLQ.
"""

import pytest

from tests.unit._helpers import lambda_context, sqs_event

pytestmark = pytest.mark.unit


def test_handler_marks_failed_items_when_email_throws(monkeypatch):
    # Arrange: la persistencia retorna persisted=True; SES levanta
    from controllers.worker import process as process_module
    from handler import lambda_handler

    persist_calls: list = []

    def fake_save(msg):
        persist_calls.append(msg)
        return {
            'persisted': True,
            'contact_id': msg.contact_id,
            'created_at': msg.created_at.isoformat(),
        }

    monkeypatch.setattr(
        process_module,
        'save_contact_idempotent',
        fake_save,
    )

    def _raise_ses_error(_msg, _persist_result):
        raise RuntimeError('SES throttled: rate exceeded')

    monkeypatch.setattr(
        process_module,
        'send_owner_email_safe',
        _raise_ses_error,
    )

    event = sqs_event()
    ctx = lambda_context()

    # Act
    result = lambda_handler(event, ctx)

    # Assert: el record fallido va en batchItemFailures (SQS reintenta)
    assert result == {
        'batchItemFailures': [
            {'itemIdentifier': '019e5c50-0000-7000-8000-msg00000001'},
        ],
    }
    # Assert: la persistencia se intento una vez (antes del fallo de SES)
    assert len(persist_calls) == 1
