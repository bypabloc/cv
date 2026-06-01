"""EmailDispatchService.publish_account_disabled — invoca send_email.

Given una cuenta deshabilitada por un admin,
When se invoca publish_account_disabled,
Then invoca send_email async con kind account-disabled, data {'reason': ...}
y el contrato EmailSendRequest (to lista, sin user_id/niche/subject_id).
"""


def test_email_dispatch_account_disabled_invokes_send_email(monkeypatch):
    from services import email_dispatch_service

    captured = {}

    def fake_invoke(*, function_name, payload):
        captured['function_name'] = function_name
        captured['payload'] = payload

    monkeypatch.setattr(email_dispatch_service, 'invoke_async', fake_invoke)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_account_disabled(
        to='u@example.com',
        user_id='user-1',
        niche=None,
        reason='abuse',
    )

    payload = captured['payload']
    data = payload['data']
    assert result is None
    assert captured['function_name'] == 'portfolio-send-email-test'
    assert payload['operation'] == 'email'
    assert payload['action'] == 'send'
    assert set(data.keys()) == {'kind', 'to', 'data'}
    assert data['kind'] == 'account-disabled'
    assert data['to'] == ['u@example.com']
    assert data['data'] == {'reason': 'abuse'}
