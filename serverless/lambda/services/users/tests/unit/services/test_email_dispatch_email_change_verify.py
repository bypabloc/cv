"""EmailDispatchService.publish_email_change_verify — invoca send_email.

Given un cambio de email pendiente de confirmacion,
When se invoca publish_email_change_verify,
Then invoca send_email async con kind email-change-verify, data con
new_email + verify_url + expires_in_min, y el contrato EmailSendRequest
(to lista, sin user_id/niche/subject_id).
"""


def test_email_dispatch_email_change_verify_invokes_send_email(monkeypatch):
    from services import email_dispatch_service

    captured = {}

    def fake_invoke(*, function_name, payload):
        captured['function_name'] = function_name
        captured['payload'] = payload

    monkeypatch.setattr(email_dispatch_service, 'invoke_async', fake_invoke)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_email_change_verify(
        to='new@example.com',
        user_id='user-1',
        niche='fintech',
        new_email='new@example.com',
        verify_url='https://x/confirm',
        expires_in_min=15,
    )

    payload = captured['payload']
    data = payload['data']
    assert result is None
    assert captured['function_name'] == 'portfolio-send-email-test'
    assert set(data.keys()) == {'kind', 'to', 'data'}
    assert data['kind'] == 'email-change-verify'
    assert data['to'] == ['new@example.com']
    assert data['data'] == {
        'new_email': 'new@example.com',
        'verify_url': 'https://x/confirm',
        'expires_in_min': 15,
    }
