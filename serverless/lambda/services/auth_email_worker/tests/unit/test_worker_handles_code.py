"""Test: Process.execute() envia email y audita para register-code.

Given un mensaje SQS valido de tipo `register-code` con un `code` de 8
     chars,
When el controller Process.execute() corre con send_email + audit
     mockeados al exito,
Then send_auth_email se llama con el code renderizado en text_body y
     log_email_audit registra `email.sent.register-code`.

AC del plan 01-auth-infra-basics: el worker envia codes via SES.
"""

import pytest

from tests.unit._helpers import code_message

pytestmark = pytest.mark.unit


def test_process_controller_sends_code_and_audits(monkeypatch):
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

    body = code_message(kind='register-code', code='7F3KQ29X')
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
            'kind': 'register-code',
            'message_id': 'fake-ses-message-id',
        },
        'code': 0,
    }

    # Assert: el code esta renderizado en text_body y html_body
    assert len(send_calls) == 1
    call = send_calls[0]
    assert call['to'] == body['to']
    assert call['subject'] == 'Tu codigo de verificacion'
    assert '7F3KQ29X' in call['text_body']
    assert '7F3KQ29X' in call['html_body']

    # Assert: audit log
    assert len(audit_calls) == 1
    audit = audit_calls[0]
    assert audit['event'] == 'email.sent.register-code'
    assert audit['success'] is True
    assert audit['user_id'] == body['user_id']
