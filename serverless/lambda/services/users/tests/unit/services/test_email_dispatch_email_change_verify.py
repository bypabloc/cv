"""EmailDispatchService.publish_email_change_verify — payload shape.

Given un cambio de email pendiente de confirmacion,
When se invoca publish_email_change_verify,
Then publica a la cola un payload con kind/to/user_id/niche/subject_id/data
y SIN schema_version ni locale.
"""



def test_email_dispatch_email_change_verify_payload(monkeypatch):
    from services import email_dispatch_service

    captured = {}

    def fake_send(*, queue_short_name, payload):
        captured['queue'] = queue_short_name
        captured['payload'] = payload
        return 'msg-1'

    monkeypatch.setattr(email_dispatch_service, 'send_to_queue', fake_send)

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
    assert result == 'msg-1'
    assert payload['kind'] == 'email-change-verify'
    assert payload['to'] == 'new@example.com'
    assert payload['user_id'] == 'user-1'
    assert payload['niche'] == 'fintech'
    assert payload['subject_id'] == 'auth.users.email-change-verify.subject'
    assert payload['data'] == {
        'new_email': 'new@example.com',
        'verify_url': 'https://x/confirm',
        'expires_in_min': 15,
    }
    assert 'schema_version' not in payload
    assert 'locale' not in payload
