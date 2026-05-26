"""Test: Process.execute() persiste y envia email cuando el contact es nuevo.

Given un mensaje SQS valido de un contact nunca visto antes,
When el controller Process.execute() corre,
Then save_contact_idempotent retorna persisted=True y send_owner_email_safe
     se llama exactamente una vez con el mensaje + persist_result.

AC-9: el worker persiste correctamente en Neon.
"""

import pytest

from tests.unit._helpers import message_body

pytestmark = pytest.mark.unit


def test_process_controller_persists_and_sends_email(monkeypatch):
    # Arrange: stub de los services
    from controllers.worker import process as process_module
    from controllers.worker.process import Process
    from models.message import ContactQueueMessage

    persist_calls: list[ContactQueueMessage] = []

    def fake_save(msg):
        persist_calls.append(msg)
        return {
            'persisted': True,
            'contact_id': msg.contact_id,
            'created_at': msg.created_at.isoformat(),
        }

    email_calls: list[tuple[ContactQueueMessage, dict]] = []

    def fake_send(msg, persist_result):
        email_calls.append((msg, persist_result))
        return 'fake-ses-message-id'

    monkeypatch.setattr(
        process_module,
        'save_contact_idempotent',
        fake_save,
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

    # Assert: respuesta del controller
    assert result == {
        'is_valid': True,
        'data': {
            'contact_id': body['contact_id'],
            'persisted': True,
        },
        'code': 0,
    }

    # Assert: la persistencia se llamo una vez con el mensaje
    assert len(persist_calls) == 1
    assert persist_calls[0].contact_id == body['contact_id']

    # Assert: el email se envio una sola vez con el mensaje + persist_result
    assert len(email_calls) == 1
    sent_msg, sent_persist = email_calls[0]
    assert sent_msg.contact_id == body['contact_id']
    assert sent_persist == {
        'persisted': True,
        'contact_id': body['contact_id'],
        'created_at': '2026-05-25T18:00:00+00:00',
    }
