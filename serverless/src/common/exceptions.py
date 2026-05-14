"""
Excepciones custom del backend.

Jerarquia (ApplicationError es la base):

    ApplicationError
    +-- ValidationError       (HTTP 400, input invalido)
    +-- TurnstileError        (HTTP 403, token CF invalido/expirado)
    +-- RateLimitExceededError (HTTP 429, sliding window agotado)
    |     +-- IPBlacklistedError    (HTTP 403, IP en blacklist)
    |     +-- CountryBlockedError   (HTTP 403, country en blacklist)

Cada excepcion guarda:
- message: descripcion para logs (no para usuario)
- code: identifier estable para clientes (ej: 'INVALID_EMAIL', 'CAPTCHA_FAILED')
- extra: dict con context adicional (no se serializa por default)
- status_code: HTTP code por defecto cuando se mapea a json_response

Uso:
    raise ValidationError(
        'Email format invalido',
        code='INVALID_EMAIL',
        extra={'value': '<redacted>'},
    )
"""

from typing import Any


class ApplicationError(Exception):
    """Excepcion base del backend. NUNCA instanciar directamente."""

    default_code = 'APPLICATION_ERROR'
    status_code = 500

    def __init__(
        self,
        message: str = '',
        *,
        code: str | None = None,
        extra: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.extra: dict[str, Any] = extra or {}
        if status_code is not None:
            self.status_code = status_code


class ValidationError(ApplicationError):
    """Input invalido (schema, formato, longitud)."""

    default_code = 'VALIDATION_ERROR'
    status_code = 400


class TurnstileError(ApplicationError):
    """Token Cloudflare Turnstile invalido, expirado o ausente."""

    default_code = 'CAPTCHA_FAILED'
    status_code = 403


class RateLimitExceededError(ApplicationError):
    """Limite sliding window agotado para el IP+endpoint."""

    default_code = 'RATE_LIMIT_EXCEEDED'
    status_code = 429

    def __init__(
        self,
        message: str = '',
        *,
        retry_after_seconds: int = 60,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after_seconds = retry_after_seconds
        self.extra.setdefault('retry_after_seconds', retry_after_seconds)


class IPBlacklistedError(RateLimitExceededError):
    """IP en blacklist (manual o auto-blacklist por bot detection)."""

    default_code = 'IP_BLACKLISTED'
    status_code = 403


class CountryBlockedError(RateLimitExceededError):
    """Country en blacklist por rate-limit rule."""

    default_code = 'COUNTRY_BLOCKED'
    status_code = 403
