"""shared.crypto.captcha.verify_captcha_or_bypass — orquestador.

Cubre el punto de decision CAPTCHA-real-vs-bypass:
- cf_response presente -> delega a verify_turnstile_token (CAPTCHA real).
- cf_response vacio + prod -> CAPTCHA_INVALID (bypass NUNCA en prod) [AC-1].
- cf_response vacio + dev + token valido -> bypassed=True [AC-2].
- cf_response vacio + dev + token invalido -> CAPTCHA_INVALID [AC-3].
- cf_response vacio + dev + sin token -> CAPTCHA_INVALID.
"""

from __future__ import annotations

import time

import pytest
import shared.crypto.captcha as captcha
from shared.core.exceptions import TurnstileError
from shared.crypto.bypass_token import sign_bypass_token
from shared.crypto.ed25519 import generate_keypair

pytestmark = pytest.mark.unit


def _make_token(stage: str) -> tuple[str, str]:
    """Devuelve (token firmado para stage, public_key_b64)."""
    private_b64, public_b64 = generate_keypair()
    token = sign_bypass_token(
        stage=stage,
        private_key_b64=private_b64,
        now=int(time.time()),
    )
    return token, public_b64


def test_cf_response_present_delegates_to_turnstile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given cf_response no vacio, When verify, Then delega a Turnstile real."""
    captured: dict[str, object] = {}

    def _fake_verify(cf_response: str, *, remote_ip: str | None = None) -> dict:
        captured['cf'] = cf_response
        captured['ip'] = remote_ip
        return {'success': True, 'hostname': 'the-full-stack.com'}

    # El import es diferido dentro de la funcion -> parchear el modulo origen.
    import shared.http.turnstile as turnstile_mod

    monkeypatch.setattr(turnstile_mod, 'verify_turnstile_token', _fake_verify)

    result = captcha.verify_captcha_or_bypass(
        'real-cf-token',
        remote_ip='1.2.3.4',
        bypass_token='ignored',
        stage='dev',
    )

    assert result['success'] is True
    assert captured == {'cf': 'real-cf-token', 'ip': '1.2.3.4'}


def test_empty_cf_in_prod_rejects_even_with_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given cf vacio + STAGE=prod + token valido, Then CAPTCHA_INVALID [AC-1]."""
    token, public_b64 = _make_token('prod')
    monkeypatch.setattr(captcha, '_load_public_key', lambda: public_b64)

    with pytest.raises(TurnstileError) as exc_info:
        captcha.verify_captcha_or_bypass(
            '',
            remote_ip='1.2.3.4',
            bypass_token=token,
            stage='prod',
        )

    assert exc_info.value.code == 'CAPTCHA_INVALID'


def test_empty_cf_in_dev_with_valid_token_bypasses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given cf vacio + STAGE=dev + token valido, Then bypassed=True [AC-2]."""
    token, public_b64 = _make_token('dev')
    monkeypatch.setattr(captcha, '_load_public_key', lambda: public_b64)

    result = captcha.verify_captcha_or_bypass(
        '',
        remote_ip='1.2.3.4',
        bypass_token=token,
        stage='dev',
    )

    assert result == {
        'success': True,
        'hostname': 'bypass',
        'bypassed': True,
    }


def test_empty_cf_in_dev_with_invalid_token_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given cf vacio + dev + token con firma mala, Then CAPTCHA_INVALID [AC-3]."""
    # Token firmado para 'dev' pero verificado contra OTRA publica.
    token, _ = _make_token('dev')
    _, other_public = generate_keypair()
    monkeypatch.setattr(captcha, '_load_public_key', lambda: other_public)

    with pytest.raises(TurnstileError) as exc_info:
        captcha.verify_captcha_or_bypass(
            '',
            remote_ip='1.2.3.4',
            bypass_token=token,
            stage='dev',
        )

    assert exc_info.value.code == 'CAPTCHA_INVALID'


def test_empty_cf_in_dev_without_token_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given cf vacio + dev + sin token, Then CAPTCHA_INVALID."""
    monkeypatch.setattr(captcha, '_load_public_key', lambda: 'unused')

    with pytest.raises(TurnstileError) as exc_info:
        captcha.verify_captcha_or_bypass(
            '',
            remote_ip='1.2.3.4',
            bypass_token=None,
            stage='dev',
        )

    assert exc_info.value.code == 'CAPTCHA_INVALID'


def test_empty_cf_in_dev_without_public_key_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given cf vacio + dev + token + sin publica configurada, Then rechaza."""
    token, _ = _make_token('dev')
    monkeypatch.setattr(captcha, '_load_public_key', lambda: '')

    with pytest.raises(TurnstileError) as exc_info:
        captcha.verify_captcha_or_bypass(
            '',
            remote_ip='1.2.3.4',
            bypass_token=token,
            stage='dev',
        )

    assert exc_info.value.code == 'CAPTCHA_INVALID'


def test_stage_resolved_from_env_when_not_passed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given stage no pasado, When verify, Then usa env STAGE (prod default)."""
    monkeypatch.delenv('STAGE', raising=False)
    token, public_b64 = _make_token('prod')
    monkeypatch.setattr(captcha, '_load_public_key', lambda: public_b64)

    # Sin STAGE en env -> default 'prod' -> bypass no aplica.
    with pytest.raises(TurnstileError) as exc_info:
        captcha.verify_captcha_or_bypass(
            '',
            remote_ip='1.2.3.4',
            bypass_token=token,
        )

    assert exc_info.value.code == 'CAPTCHA_INVALID'
