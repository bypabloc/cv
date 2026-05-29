"""EmailDispatchService (auth) — publica payloads que el worker ACEPTA.

Contrato del worker (`auth_email_worker/core/models/message.py`,
`AuthEmailMessage` con `extra='forbid'`): el payload top-level debe ser
EXACTAMENTE `{kind, to, user_id, niche, subject_id, data}`. Cualquier
campo extra (`schema_version`, `locale`) o `subject_id` ausente hace
fallar la validacion en el worker -> el mensaje termina en la DLQ sin
enviarse. Estos tests son el guard de regresion de ese contrato.
"""

from unittest.mock import MagicMock

# Conjunto EXACTO de claves top-level que el worker (AuthEmailMessage)
# acepta. Si el productor agrega/quita una, el worker rechaza el mensaje.
_WORKER_TOP_LEVEL_KEYS = {'kind', 'to', 'user_id', 'niche', 'subject_id', 'data'}


def test_publish_magic_link_sends_worker_compatible_payload(monkeypatch):
    """
    Given un magic-link de register,
    When publish_magic_link encola el mensaje,
    Then el payload tiene el shape exacto de AuthEmailMessage (subject_id
         presente, sin schema_version/locale) y data lleva verify_url +
         expires_in_min.
    """
    from services import email_dispatch_service

    fake_send = MagicMock(return_value='msg-id-1')
    monkeypatch.setattr(email_dispatch_service, 'send_to_queue', fake_send)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    msg_id = svc.publish_magic_link(
        to='visitor@example.com',
        user_id='user-1',
        niche='fintech',
        kind='register-magic-link',
        verify_url='https://api.example.com/auth?token=OPAQUE_PLAIN',
        expires_in_min=15,
    )

    assert msg_id == 'msg-id-1'
    payload = fake_send.call_args.kwargs['payload']

    # Shape exacto del worker: ni un campo de mas, ni uno de menos.
    assert set(payload.keys()) == _WORKER_TOP_LEVEL_KEYS
    assert 'schema_version' not in payload
    assert 'locale' not in payload

    assert payload['kind'] == 'register-magic-link'
    assert payload['to'] == 'visitor@example.com'
    assert payload['user_id'] == 'user-1'
    assert payload['niche'] == 'fintech'
    assert payload['subject_id'] == 'auth.register-magic-link.subject'
    assert payload['data'] == {
        'verify_url': 'https://api.example.com/auth?token=OPAQUE_PLAIN',
        'expires_in_min': 15,
    }


def test_publish_code_sends_worker_compatible_payload(monkeypatch):
    """
    Given un code de register,
    When publish_code encola el mensaje,
    Then el payload tiene el shape exacto de AuthEmailMessage y data lleva
         code + expires_in_min.
    """
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
        expires_in_min=15,
    )

    assert msg_id == 'msg-id-2'
    payload = fake_send.call_args.kwargs['payload']

    assert set(payload.keys()) == _WORKER_TOP_LEVEL_KEYS
    assert 'schema_version' not in payload
    assert 'locale' not in payload

    assert payload['kind'] == 'register-code'
    assert payload['user_id'] == 'user-1'
    assert payload['niche'] is None
    assert payload['subject_id'] == 'auth.register-code.subject'
    assert payload['data'] == {'code': 'ABCDEFGH', 'expires_in_min': 15}
