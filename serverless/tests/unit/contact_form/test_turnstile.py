"""Tests para contact_form.turnstile (httpx con respx)."""

from __future__ import annotations

import httpx
import pytest
import respx

from common.exceptions import TurnstileError
from contact_form.turnstile import (
    TURNSTILE_SITEVERIFY_URL,
    verify_turnstile_token,
)

pytestmark = pytest.mark.unit


class TestVerifyTurnstileToken:
    """verify_turnstile_token - flujo completo."""

    @respx.mock
    def test_when_success_then_returns_response(
        self, contact_form_aws: None
    ) -> None:
        """
        Given Cloudflare retorna success=true + hostname valido,
        When verify_turnstile_token,
        Then retorna el dict.
        """
        respx.post(TURNSTILE_SITEVERIFY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    'success': True,
                    'hostname': 'the-full-stack.com',
                    'challenge_ts': '2026-05-14T15:00:00Z',
                },
            )
        )

        result = verify_turnstile_token('valid-cf-response', remote_ip='1.2.3.4')

        assert result['success'] is True
        assert result['hostname'] == 'the-full-stack.com'

    @respx.mock
    def test_when_success_false_then_raises_captcha_invalid(
        self, contact_form_aws: None
    ) -> None:
        """Given success=false, When verify, Then TurnstileError CAPTCHA_INVALID."""
        respx.post(TURNSTILE_SITEVERIFY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    'success': False,
                    'error-codes': ['invalid-input-response'],
                },
            )
        )

        with pytest.raises(TurnstileError) as exc_info:
            verify_turnstile_token('bad-cf-response', remote_ip='1.2.3.4')

        assert exc_info.value.code == 'CAPTCHA_INVALID'
        assert exc_info.value.extra['error_codes'] == ['invalid-input-response']

    @respx.mock
    def test_when_hostname_mismatch_then_raises(
        self, contact_form_aws: None
    ) -> None:
        """
        Given hostname no esta en whitelist,
        When verify,
        Then TurnstileError CAPTCHA_HOSTNAME_MISMATCH.
        """
        respx.post(TURNSTILE_SITEVERIFY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    'success': True,
                    'hostname': 'evil.com',
                },
            )
        )

        with pytest.raises(TurnstileError) as exc_info:
            verify_turnstile_token('cf-response-value', remote_ip='1.2.3.4')

        assert exc_info.value.code == 'CAPTCHA_HOSTNAME_MISMATCH'

    @respx.mock
    @pytest.mark.parametrize(
        'hostname',
        [
            'hub.localhost',
            'fintech.localhost',
            'architect.localhost',
            'leader.localhost',
            'vibe.localhost',
        ],
    )
    def test_when_localhost_subdomain_in_stage_dev_then_allowed(
        self,
        contact_form_aws: None,
        monkeypatch: pytest.MonkeyPatch,
        hostname: str,
    ) -> None:
        """
        Given hostname *.localhost + STAGE=dev,
        When verify,
        Then aceptado (RFC 6761 garantiza resolucion local).
        """
        monkeypatch.setenv('STAGE', 'dev')
        respx.post(TURNSTILE_SITEVERIFY_URL).mock(
            return_value=httpx.Response(
                200,
                json={'success': True, 'hostname': hostname},
            )
        )

        result = verify_turnstile_token('cf-response-value', remote_ip='1.2.3.4')

        assert result['success'] is True
        assert result['hostname'] == hostname

    @respx.mock
    def test_when_localhost_subdomain_in_stage_prod_then_rejected(
        self, contact_form_aws: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given hostname *.localhost + STAGE=prod,
        When verify,
        Then rechazado (subdominios localhost solo en dev).
        """
        monkeypatch.setenv('STAGE', 'prod')
        respx.post(TURNSTILE_SITEVERIFY_URL).mock(
            return_value=httpx.Response(
                200,
                json={'success': True, 'hostname': 'architect.localhost'},
            )
        )

        with pytest.raises(TurnstileError) as exc_info:
            verify_turnstile_token('cf-response-value', remote_ip='1.2.3.4')

        assert exc_info.value.code == 'CAPTCHA_HOSTNAME_MISMATCH'

    @respx.mock
    def test_when_evil_localhost_subdomain_then_rejected(
        self, contact_form_aws: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given hostname disfrazado tipo evil.localhost.attacker.com,
        When verify,
        Then rechazado (pattern enforce $ anclado).
        """
        monkeypatch.setenv('STAGE', 'dev')
        respx.post(TURNSTILE_SITEVERIFY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    'success': True,
                    'hostname': 'evil.localhost.attacker.com',
                },
            )
        )

        with pytest.raises(TurnstileError) as exc_info:
            verify_turnstile_token('cf-response-value', remote_ip='1.2.3.4')

        assert exc_info.value.code == 'CAPTCHA_HOSTNAME_MISMATCH'

    def test_when_bypass_secret_matches_then_skip_verify(
        self, contact_form_aws: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given TURNSTILE_BYPASS_SECRET seteado + header matchea,
        When verify,
        Then skip Cloudflare API (no HTTP call).
        """
        monkeypatch.setenv('TURNSTILE_BYPASS_SECRET', 'test-bypass-123')

        result = verify_turnstile_token(
            'any-cf-response',
            remote_ip='1.2.3.4',
            bypass_secret='test-bypass-123',  # noqa: S106
        )

        assert result['success'] is True
        assert result.get('bypassed') is True

    def test_when_bypass_secret_wrong_then_does_not_skip(
        self, contact_form_aws: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given bypass_secret no matchea,
        When verify,
        Then NO skip (intenta llamar a Cloudflare).
        """
        monkeypatch.setenv('TURNSTILE_BYPASS_SECRET', 'real-secret')

        # respx no activado -> la llamada HTTP es real y falla. Cae en
        # TurnstileError CAPTCHA_FAILED por connection error.
        with pytest.raises(TurnstileError):
            verify_turnstile_token(
                'any-cf-response',
                remote_ip='1.2.3.4',
                bypass_secret='wrong-secret',  # noqa: S106
            )
