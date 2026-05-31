"""EmailDispatchService.publish_email_changed — invoca send_email.

Given un email cambiado (notificacion al email VIEJO),
When se invoca publish_email_changed,
Then invoca send_email async con kind email-changed, data {'new_email': ...}
y el contrato EmailSendRequest (to lista, sin user_id/niche/subject_id).
"""


def test_email_dispatch_email_changed_invokes_send_email(monkeypatch):
    from services import email_dispatch_service

    captured = {}

    def fake_invoke(*, function_name, payload):
        captured['function_name'] = function_name
        captured['payload'] = payload

    monkeypatch.setattr(email_dispatch_service, 'invoke_async', fake_invoke)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_email_changed(
        to='old@example.com',
        user_id='user-1',
        niche='leader',
        new_email='new@example.com',
    )

    payload = captured['payload']
    data = payload['data']
    assert result is None
    assert captured['function_name'] == 'portfolio-send-email-test'
    assert set(data.keys()) == {'kind', 'to', 'data'}
    assert data['kind'] == 'email-changed'
    assert data['to'] == ['old@example.com']
    assert data['data'] == {'new_email': 'new@example.com'}
