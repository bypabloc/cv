"""Unit tests para common.exceptions."""

from __future__ import annotations

import pytest

from common.exceptions import (
    ApplicationError,
    CountryBlockedError,
    IPBlacklistedError,
    RateLimitExceededError,
    TurnstileError,
    ValidationError,
)

pytestmark = pytest.mark.unit


class TestApplicationError:
    """ApplicationError - excepcion base + defaults."""

    def test_when_default_then_500_status_application_error_code(self) -> None:
        """Given sin args, When raise ApplicationError, Then status 500 + code APPLICATION_ERROR."""
        err = ApplicationError('boom')

        assert err.message == 'boom'
        assert err.code == 'APPLICATION_ERROR'
        assert err.status_code == 500
        assert err.extra == {}

    def test_when_override_status_then_uses_override(self) -> None:
        """Given status_code override, When raise, Then usa override."""
        err = ApplicationError('boom', status_code=503)

        assert err.status_code == 503


class TestValidationError:
    """ValidationError - HTTP 400."""

    def test_inherits_application_error_with_400(self) -> None:
        """Given ValidationError, Then status 400 + code VALIDATION_ERROR."""
        err = ValidationError('bad input')

        assert isinstance(err, ApplicationError)
        assert err.status_code == 400
        assert err.code == 'VALIDATION_ERROR'

    def test_when_override_code_then_uses_override(self) -> None:
        """Given code custom, When raise, Then preserva el custom."""
        err = ValidationError('email invalido', code='INVALID_EMAIL')

        assert err.code == 'INVALID_EMAIL'


class TestTurnstileError:
    """TurnstileError - HTTP 403."""

    def test_default_403_captcha_failed(self) -> None:
        """Given TurnstileError, Then status 403 + CAPTCHA_FAILED."""
        err = TurnstileError('token invalido')

        assert err.status_code == 403
        assert err.code == 'CAPTCHA_FAILED'


class TestRateLimitExceededError:
    """RateLimitExceededError - HTTP 429 + retry_after."""

    def test_default_429_with_retry_after_60s(self) -> None:
        """Given sin retry_after, Then default 60s."""
        err = RateLimitExceededError('too many')

        assert err.status_code == 429
        assert err.retry_after_seconds == 60
        assert err.extra['retry_after_seconds'] == 60

    def test_when_custom_retry_after_then_propagated_to_extra(self) -> None:
        """Given retry_after=300, Then preserva en extra dict."""
        err = RateLimitExceededError('throttled', retry_after_seconds=300)

        assert err.retry_after_seconds == 300
        assert err.extra['retry_after_seconds'] == 300


class TestIPBlacklistedError:
    """IPBlacklistedError - hereda de RateLimit con HTTP 403."""

    def test_inherits_from_rate_limit_with_403(self) -> None:
        """Given IPBlacklistedError, Then 403 + IP_BLACKLISTED."""
        err = IPBlacklistedError('banned IP', retry_after_seconds=86400)

        assert isinstance(err, RateLimitExceededError)
        assert err.status_code == 403
        assert err.code == 'IP_BLACKLISTED'
        assert err.retry_after_seconds == 86400


class TestCountryBlockedError:
    """CountryBlockedError - hereda de RateLimit con HTTP 403."""

    def test_inherits_from_rate_limit_with_403(self) -> None:
        """Given CountryBlockedError, Then 403 + COUNTRY_BLOCKED."""
        err = CountryBlockedError('CN blocked')

        assert err.status_code == 403
        assert err.code == 'COUNTRY_BLOCKED'


def test_exceptions_can_be_raised_and_caught() -> None:
    """
    Given todas las excepciones,
    When raise/catch,
    Then funcionan como exceptions normales.
    """
    with pytest.raises(ApplicationError):
        raise ValidationError('test')

    with pytest.raises(RateLimitExceededError):
        raise IPBlacklistedError('test', retry_after_seconds=10)
