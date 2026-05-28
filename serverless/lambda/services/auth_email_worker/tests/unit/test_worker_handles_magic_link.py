"""Test: Process.execute() envia email y audita para register-magic-link.

Given un mensaje SQS valido de tipo `register-magic-link`,
When el controller Process.execute() corre con send_email + audit
     mockeados al exito,
Then send_auth_email se llama con to=[mensaje.to] y subject + body
     renderizados, y log_email_audit registra `email.sent.register-magic-link`.

AC del plan 01-auth-infra-basics: el worker envia magic-links via SES y
audita el evento.
"""

import pytest

from tests.unit._helpers import magic_link_message

pytestmark = pytest.mark.unit


def test_process_controller_sends_magic_link_and_audits(monkeypatch):
    # Arrange
    from controllers.email import process as process_module
    from controllers.email.process import Process
    from models.message import AuthEmailMessage

    send_calls: list[dict] = []

    def fake_send(*, to, subject, text_body, html_body):
        send_calls.append({
            'to': to,
            'subject': subject,
            'text_body': text_body,
            'html_body': html_body,
        })
        return 'fake-ses-message-id'

    audit_calls: list[dict] = []

    def fake_audit(**kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr(process_module, 'send_auth_email', fake_send)
    monkeypatch.setattr(process_module, 'log_email_audit', fake_audit)

    body = magic_link_message(kind='register-magic-link')
    msg = AuthEmailMessage.model_validate(body)
    controller = Process(event=body)
    controller.validated_data = msg

    # Act
    result = controller.execute()

    # Assert: respuesta del controller
    assert result == {
        'is_valid': True,
        'data': {
            'sent': True,
            'kind': 'register-magic-link',
            'message_id': 'fake-ses-message-id',
        },
        'code': 0,
    }

    # Assert: SES llamado una sola vez con el destinatario del mensaje
    assert len(send_calls) == 1
    call = send_calls[0]
    assert call['to'] == body['to']
    assert call['subject'] == 'Activa tu cuenta en the-full-stack.com'
    # El verify_url debe haber sido renderizado en el text body
    assert body['data']['verify_url'] in call['text_body']
    assert str(body['data']['expires_in_min']) in call['text_body']
    # El HTML tambien lleva el link
    assert body['data']['verify_url'] in call['html_body']

    # Assert: audit log registrado como exito para el kind correcto
    assert len(audit_calls) == 1
    audit = audit_calls[0]
    assert audit['event'] == 'email.sent.register-magic-link'
    assert audit['success'] is True
    assert audit['user_id'] == body['user_id']
    assert audit['meta']['message_id'] == 'fake-ses-message-id'
