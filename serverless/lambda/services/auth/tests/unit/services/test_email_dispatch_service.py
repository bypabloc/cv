"""EmailDispatchService (auth) — invoca send_email con el contrato correcto.

Contrato de `send_email` (`EmailSendRequest` con `extra='forbid'`): el `data`
del evento `{operation:'email', action:'send', data}` debe ser EXACTAMENTE
`{kind, to, data, reply_to?}`. `to` es una lista; `data` lleva SOLO los
placeholders Jinja2 del template (NO user_id/niche/subject_id — el subject
sale de `email-config`). Estos tests son el guard de regresion de ese
contrato: el invoke se mockea y se assertea el payload.
"""

from __future__ import annotations

from unittest.mock import MagicMock

# Conjunto EXACTO de claves del `data` del evento que send_email acepta
# (EmailSendRequest, extra='forbid'). reply_to es opcional y solo lo usa
# contact_form; auth NO lo manda.
_SEND_EMAIL_DATA_KEYS = {'kind', 'to', 'data'}


def test_publish_magic_link_invokes_send_email(monkeypatch):
    """
    Given un magic-link de register,
    When publish_magic_link se invoca,
    Then invoca send_email async con el contrato EmailSendRequest (to lista,
         data solo verify_url + expires_in_min, sin user_id/niche/subject_id).
    """
    from services import email_dispatch_service

    fake_invoke = MagicMock()
    monkeypatch.setattr(email_dispatch_service, 'invoke_async', fake_invoke)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_magic_link(
        to='visitor@example.com',
        user_id='user-1',
        niche='fintech',
        kind='register-magic-link',
        verify_url='https://api.example.com/auth?token=OPAQUE_PLAIN',
        expires_in_min=15,
    )

    assert result is None
    fname = fake_invoke.call_args.kwargs['function_name']
    payload = fake_invoke.call_args.kwargs['payload']

    assert fname == 'portfolio-send-email-test'
    assert payload['operation'] == 'email'
    assert payload['action'] == 'send'

    data = payload['data']
    assert set(data.keys()) == _SEND_EMAIL_DATA_KEYS
    assert data['kind'] == 'register-magic-link'
    assert data['to'] == ['visitor@example.com']
    assert data['data'] == {
        'verify_url': 'https://api.example.com/auth?token=OPAQUE_PLAIN',
        'expires_in_min': 15,
    }


def test_publish_code_invokes_send_email(monkeypatch):
    """
    Given un code de register,
    When publish_code se invoca,
    Then invoca send_email async con data = {code, expires_in_min} y to lista.
    """
    from services import email_dispatch_service

    fake_invoke = MagicMock()
    monkeypatch.setattr(email_dispatch_service, 'invoke_async', fake_invoke)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_code(
        to='visitor@example.com',
        user_id='user-1',
        niche=None,
        kind='register-code',
        code='ABCDEFGH',
        expires_in_min=15,
    )

    assert result is None
    payload = fake_invoke.call_args.kwargs['payload']
    data = payload['data']

    assert set(data.keys()) == _SEND_EMAIL_DATA_KEYS
    assert data['kind'] == 'register-code'
    assert data['to'] == ['visitor@example.com']
    assert data['data'] == {'code': 'ABCDEFGH', 'expires_in_min': 15}


def test_publish_unified_invokes_send_email(monkeypatch):
    """
    Given un email unificado (magic-link + code juntos),
    When publish_unified se invoca,
    Then hace UN solo invoke a send_email con data = {verify_url, code,
         expires_in_min} y to lista (1 email en vez de 2).
    """
    from services import email_dispatch_service

    fake_invoke = MagicMock()
    monkeypatch.setattr(email_dispatch_service, 'invoke_async', fake_invoke)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_unified(
        to='visitor@example.com',
        user_id='user-1',
        niche='fintech',
        kind='register-unified',
        verify_url='https://api.example.com/auth?token=OPAQUE_PLAIN',
        code='ABCDEFGH',
        expires_in_min=15,
    )

    assert result is None
    assert fake_invoke.call_count == 1
    payload = fake_invoke.call_args.kwargs['payload']
    data = payload['data']

    assert set(data.keys()) == _SEND_EMAIL_DATA_KEYS
    assert data['kind'] == 'register-unified'
    assert data['to'] == ['visitor@example.com']
    assert data['data'] == {
        'verify_url': 'https://api.example.com/auth?token=OPAQUE_PLAIN',
        'code': 'ABCDEFGH',
        'expires_in_min': 15,
    }


def test_publish_does_not_raise_when_invoke_fails(monkeypatch):
    """
    Given que el invoke a send_email lanza LambdaInvokeError,
    When publish_code se invoca,
    Then NO propaga la excepcion (best-effort: el code ya quedo persistido).
    """
    from services import email_dispatch_service
    from shared.aws.lambda_invoke import LambdaInvokeError

    def _raise(*, function_name: str, payload: dict) -> None:
        raise LambdaInvokeError(f'invoke_async to {function_name} failed')

    monkeypatch.setattr(email_dispatch_service, 'invoke_async', _raise)

    svc = email_dispatch_service.EmailDispatchService(app_config=object())
    result = svc.publish_code(
        to='visitor@example.com',
        user_id='user-1',
        niche=None,
        kind='login-code',
        code='ABCDEFGH',
        expires_in_min=15,
    )

    assert result is None
