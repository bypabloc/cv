"""EmailDispatchService.publish_account_deleted — invoca send_email.

Given una cuenta eliminada,
When se invoca publish_account_deleted,
Then invoca send_email async con kind account-deleted, data {} y el
contrato EmailSendRequest (to lista, sin user_id/niche/subject_id).
"""


def test_email_dispatch_account_deleted_invokes_send_email(monkeypatch):
    from services import email_dispatch_service

    captured = {}

    def fake_invoke(*, function_name, payload):
        captured['function_name'] = function_name
        captured['payload'] = payload

    monkeypatch.setattr(email_dispatch_service, 'invoke_async', fake_invoke)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_account_deleted(
        to='u@example.com',
        user_id='user-1',
        niche='leader',
    )

    payload = captured['payload']
    data = payload['data']
    assert result is None
    assert captured['function_name'] == 'portfolio-send-email-test'
    assert set(data.keys()) == {'kind', 'to', 'data'}
    assert data['kind'] == 'account-deleted'
    assert data['to'] == ['u@example.com']
    assert data['data'] == {}
