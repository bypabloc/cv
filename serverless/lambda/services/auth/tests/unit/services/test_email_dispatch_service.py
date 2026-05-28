"""EmailDispatchService — publica payloads correctos a SQS."""

from unittest.mock import MagicMock


def test_publish_magic_link_sends_payload_with_token(monkeypatch):
    from services import email_dispatch_service

    fake_send = MagicMock(return_value='msg-id-1')
    monkeypatch.setattr(email_dispatch_service, 'send_to_queue', fake_send)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    msg_id = svc.publish_magic_link(
        to='visitor@example.com',
        user_id='user-1',
        niche='fintech',
        kind='register-magic-link',
        plain='OPAQUE_PLAIN',
        verify_url='https://api.example.com/auth?token=OPAQUE_PLAIN',
    )

    assert msg_id == 'msg-id-1'
    payload = fake_send.call_args.kwargs['payload']
    assert payload['kind'] == 'register-magic-link'
    assert payload['to'] == 'visitor@example.com'
    assert payload['data']['token'] == 'OPAQUE_PLAIN'
    assert payload['data']['verify_url'].endswith('OPAQUE_PLAIN')


def test_publish_code_sends_payload_with_code(monkeypatch):
    from services import email_dispatch_service

    fake_send = MagicMock(return_value='msg-id-2')
    monkeypatch.setattr(email_dispatch_service, 'send_to_queue', fake_send)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    msg_id = svc.publish_code(
        to='visitor@example.com',
        user_id='user-1',
        niche=None,
        kind='register-code',
        code='ABCDEFGH',
    )

    assert msg_id == 'msg-id-2'
    payload = fake_send.call_args.kwargs['payload']
    assert payload['kind'] == 'register-code'
    assert payload['data']['code'] == 'ABCDEFGH'
