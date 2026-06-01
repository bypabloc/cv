"""Controller contact/create — bypass NUNCA aplica en prod (AC-1).

Given STAGE=prod + cf_token vacio + un bypass_token (cualquiera),
When el controller Create ejecuta run(),
Then verify_captcha_or_bypass levanta TurnstileError(CAPTCHA_INVALID): el
     bypass solo existe en dev/local, prod siempre exige CAPTCHA real.
"""

import pytest
from shared.core.exceptions import TurnstileError

pytestmark = pytest.mark.unit


def _event_data(ip: str) -> dict:
    return {
        'name': 'Pablo Contreras',
        'email': 'user@example.com',
        'message': 'Hola, me interesa colaborar contigo.',
        'cf_token': '',
        '_meta': {
            'ip': ip,
            'country': 'CL',
            'user_agent': 'Mozilla/5.0',
            'bypass_token': 'any-token-value',
        },
    }


def test_bypass_rejected_in_prod(
    monkeypatch: pytest.MonkeyPatch,
    contact_form_aws: None,
) -> None:
    from controllers.contact.create import Create

    # Arrange: STAGE=prod -> el orquestador rechaza el bypass.
    monkeypatch.setenv('STAGE', 'prod')

    # Act / Assert
    with pytest.raises(TurnstileError) as exc_info:
        Create(event=_event_data('203.0.113.90')).run()

    assert exc_info.value.code == 'CAPTCHA_INVALID'


def test_bypass_accepts_valid_token_in_dev(
    monkeypatch: pytest.MonkeyPatch,
    contact_form_aws: None,
    mock_neon_writes: list[dict],
    mock_invoke: list[dict],
) -> None:
    """Given STAGE=dev + cf vacio + token firmado valido, Then acepta [AC-2]."""
    import time

    import shared.crypto.captcha as captcha_mod
    from controllers.contact.create import Create
    from shared.crypto.bypass_token import sign_bypass_token
    from shared.crypto.ed25519 import generate_keypair

    monkeypatch.setenv('STAGE', 'dev')

    private_b64, public_b64 = generate_keypair()
    monkeypatch.setattr(captcha_mod, '_load_public_key', lambda: public_b64)
    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=int(time.time()),
    )
    event = _event_data('203.0.113.91')
    event['_meta']['bypass_token'] = token

    # Act
    result = Create(event=event).run()

    # Assert: persistio inline + invoco send_email async.
    assert result['is_valid'] is True
    assert len(mock_neon_writes) == 1
    assert len(mock_invoke) == 1
