"""EmailDispatchService.publish_account_deleted — payload shape.

Given una cuenta eliminada,
When se invoca publish_account_deleted,
Then publica un payload con kind account-deleted, data {} y SIN
schema_version ni locale.
"""


def test_email_dispatch_account_deleted_payload(monkeypatch):
    from services import email_dispatch_service

    captured = {}

    def fake_send(*, queue_short_name, payload):
        captured['payload'] = payload
        return 'msg-3'

    monkeypatch.setattr(email_dispatch_service, 'send_to_queue', fake_send)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_account_deleted(
        to='u@example.com',
        user_id='user-1',
        niche='leader',
    )

    payload = captured['payload']
    assert result == 'msg-3'
    assert payload['kind'] == 'account-deleted'
    assert payload['to'] == 'u@example.com'
    assert payload['user_id'] == 'user-1'
    assert payload['niche'] == 'leader'
    assert payload['subject_id'] == 'auth.users.account-deleted.subject'
    assert payload['data'] == {}
    assert 'schema_version' not in payload
    assert 'locale' not in payload
