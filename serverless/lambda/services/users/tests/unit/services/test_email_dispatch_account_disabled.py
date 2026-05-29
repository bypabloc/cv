"""EmailDispatchService.publish_account_disabled — payload shape.

Given una cuenta deshabilitada por un admin,
When se invoca publish_account_disabled,
Then publica un payload con kind account-disabled, data {'reason': ...}
y SIN schema_version ni locale.
"""


def test_email_dispatch_account_disabled_payload(monkeypatch):
    from services import email_dispatch_service

    captured = {}

    def fake_send(*, queue_short_name, payload):
        captured['payload'] = payload
        return 'msg-2'

    monkeypatch.setattr(email_dispatch_service, 'send_to_queue', fake_send)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_account_disabled(
        to='u@example.com',
        user_id='user-1',
        niche=None,
        reason='abuse',
    )

    payload = captured['payload']
    assert result == 'msg-2'
    assert payload['kind'] == 'account-disabled'
    assert payload['to'] == 'u@example.com'
    assert payload['user_id'] == 'user-1'
    assert payload['niche'] is None
    assert payload['subject_id'] == 'auth.users.account-disabled.subject'
    assert payload['data'] == {'reason': 'abuse'}
    assert 'schema_version' not in payload
    assert 'locale' not in payload
