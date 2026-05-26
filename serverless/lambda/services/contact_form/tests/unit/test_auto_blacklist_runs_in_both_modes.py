"""Controller — auto-blacklist corre en AMBOS modos (async + sync).

Given una IP que ya supero el threshold (3+ tokens validos en 60s) — el
     mock de increment_bucket retorna `turnstile_tokens=3`,
When el controller Create ejecuta run() en modo async Y luego en modo
     sync,
Then `create_blacklist_rule` se invoca en AMBOS modos (la defensa
     anti-solver es independiente del modo de procesamiento).

Spec lambdas-async-sqs (fase 07): si el auto-blacklist solo corriera en
sync, un solver podria saturar la cola SQS sin ser bloqueado durante
todo el rollout async. AC del controller.
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL

pytestmark = pytest.mark.unit


def _event_data(ip: str) -> dict:
    return {
        'name': 'Pablo Contreras',
        'email': 'user@example.com',
        'message': 'Hola, me interesa colaborar contigo.',
        'cf_token': 'x' * 30,
        '_meta': {
            'ip': ip,
            'country': 'CL',
            'user_agent': 'Mozilla/5.0',
            'bypass_secret': None,
        },
    }


@respx.mock
def test_auto_blacklist_runs_in_async_mode(
    monkeypatch: pytest.MonkeyPatch,
    mock_sqs: list[dict],
    contact_form_aws: None,
) -> None:
    import controllers.contact.create as create_mod
    from controllers.contact.create import Create
    from settings.config import AppConfig

    # Arrange: async mode, solver cruza el threshold.
    monkeypatch.setattr(AppConfig, 'async_mode', True)

    blacklist_calls: list[str] = []

    def _spy_blacklist(ip: str) -> None:
        blacklist_calls.append(ip)

    monkeypatch.setattr(
        create_mod,
        'increment_bucket',
        lambda **_kw: {'turnstile_tokens': 3},
    )
    monkeypatch.setattr(create_mod, 'create_blacklist_rule', _spy_blacklist)

    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )

    # Act
    result = Create(event=_event_data('203.0.113.60')).run()

    # Assert
    assert result['is_valid'] is True
    assert blacklist_calls == ['203.0.113.60']
    assert len(mock_sqs) == 1


@respx.mock
def test_auto_blacklist_runs_in_sync_mode(
    monkeypatch: pytest.MonkeyPatch,
    mock_neon_writes: list[dict],
    contact_form_aws: None,
) -> None:
    import controllers.contact.create as create_mod
    from controllers.contact.create import Create
    from settings.config import AppConfig

    # Arrange: sync mode (legacy), solver cruza el threshold.
    monkeypatch.setattr(AppConfig, 'async_mode', False)

    blacklist_calls: list[str] = []

    def _spy_blacklist(ip: str) -> None:
        blacklist_calls.append(ip)

    monkeypatch.setattr(
        create_mod,
        'increment_bucket',
        lambda **_kw: {'turnstile_tokens': 3},
    )
    monkeypatch.setattr(create_mod, 'create_blacklist_rule', _spy_blacklist)

    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={'success': True, 'hostname': 'the-full-stack.com'}
        )
    )

    # Act
    result = Create(event=_event_data('203.0.113.61')).run()

    # Assert
    assert result['is_valid'] is True
    assert blacklist_calls == ['203.0.113.61']
