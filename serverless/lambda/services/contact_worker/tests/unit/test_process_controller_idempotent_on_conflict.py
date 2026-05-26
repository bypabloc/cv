"""Test: Process.execute() es idempotente cuando el contact ya existe.

Given un mensaje SQS con contact_id que YA existe en Neon (el helper
retorna persisted=False),
When Process.execute() corre,
Then data retorna {contact_id, skipped: True} y send_owner_email_safe
     NO se llama (evita email duplicado al owner por retry SQS).

AC-10: idempotencia del worker. Si SQS re-entrega el mismo mensaje, el
INSERT con ON CONFLICT (id) DO NOTHING devuelve rowcount=0 y el worker
NO manda email otra vez.
"""

import pytest

from tests.unit._helpers import message_body

pytestmark = pytest.mark.unit


def test_process_controller_skips_email_when_contact_already_persisted(
    monkeypatch,
):
    # Arrange: el helper de persistencia retorna persisted=False
    from controllers.worker import process as process_module
    from controllers.worker.process import Process
    from models.message import ContactQueueMessage

    def fake_save_already_existed(msg):
        return {
            'persisted': False,
            'contact_id': msg.contact_id,
            'created_at': msg.created_at.isoformat(),
        }

    email_calls: list[tuple] = []

    def fake_send(msg, persist_result):
        email_calls.append((msg, persist_result))
        return 'unexpected-message-id'

    monkeypatch.setattr(
        process_module,
        'save_contact_idempotent',
        fake_save_already_existed,
    )
    monkeypatch.setattr(
        process_module,
        'send_owner_email_safe',
        fake_send,
    )

    body = message_body()
    msg = ContactQueueMessage.model_validate(body)
    controller = Process(event=body)
    controller.validated_data = msg

    # Act
    result = controller.execute()

    # Assert: respuesta marca skipped
    assert result == {
        'is_valid': True,
        'data': {
            'contact_id': body['contact_id'],
            'skipped': True,
        },
        'code': 0,
    }

    # Assert: send_owner_email_safe NO se llamo (no duplica email)
    assert email_calls == []
