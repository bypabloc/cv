"""Test: lambda_handler retorna batchItemFailures vacio cuando todo OK.

Given un batch SQS con 1 mensaje valido, y la persistencia + email
mockeados al exito,
When lambda_handler procesa el batch,
Then retorna {'batchItemFailures': []} (SQS borra el mensaje).

AC-9 / AC-11: caso feliz del flujo SQS -> worker -> persistencia + email.
"""

import pytest

from tests.unit._helpers import lambda_context, sqs_event

pytestmark = pytest.mark.unit


def test_handler_returns_no_failures_on_success(monkeypatch):
    # Arrange: mock de los services dentro del controller
    from controllers.worker import process as process_module
    from handler import lambda_handler

    monkeypatch.setattr(
        process_module,
        'save_contact_idempotent',
        lambda msg: {
            'persisted': True,
            'contact_id': msg.contact_id,
            'created_at': msg.created_at.isoformat(),
        },
    )
    monkeypatch.setattr(
        process_module,
        'send_owner_email_safe',
        lambda msg, persist_result: 'ses-message-id',
    )

    event = sqs_event()
    ctx = lambda_context()

    # Act
    result = lambda_handler(event, ctx)

    # Assert: batch vacio = SQS borra todos los mensajes
    assert result == {'batchItemFailures': []}
