"""Controller — auto-blacklist corre tras un submit exitoso.

Given una IP que ya supero el threshold (AUTO_BLACKLIST_THRESHOLD CAPTCHAs
     validos en 60s) — el mock de increment_bucket retorna
     `turnstile_tokens=AUTO_BLACKLIST_THRESHOLD`,
When el controller Create ejecuta run() con exito,
Then `create_blacklist_rule` se invoca (la defensa anti-solver corre
     despues de persistir + notificar).

El auto-blacklist es la defensa anti-solver: si una IP adjunta
AUTO_BLACKLIST_THRESHOLD CAPTCHAs Turnstile validos en 60s, se asume bot con
solver y se blacklistea.
"""

import httpx
import pytest
import respx
from shared.http.turnstile import TURNSTILE_SITEVERIFY_URL
from shared.rate_limit.auto_blacklist import AUTO_BLACKLIST_THRESHOLD

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
            'bypass_token': None,
        },
    }


@respx.mock
def test_auto_blacklist_runs_after_success(
    monkeypatch: pytest.MonkeyPatch,
    mock_neon_writes: list[dict],
    mock_invoke: list[dict],
    contact_form_aws: None,
) -> None:
    import controllers.contact.create as create_mod
    from controllers.contact.create import Create

    # Arrange: solver cruza el threshold.
    blacklist_calls: list[str] = []

    def _spy_blacklist(ip: str) -> None:
        blacklist_calls.append(ip)

    monkeypatch.setattr(
        create_mod,
        'increment_bucket',
        lambda **_kw: {'turnstile_tokens': AUTO_BLACKLIST_THRESHOLD},
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
