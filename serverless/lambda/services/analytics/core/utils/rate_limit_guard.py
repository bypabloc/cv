"""Rate-limit guard del Lambda `analytics`.

Segunda capa de defensa (detras del JWT): llama a
`shared.rate_limit.check_or_raise` con la metadata extraida del request.
Levanta RateLimitExceededError / IPBlacklistedError / CountryBlockedError
que `http_handler` mapea a 429/403 con codes 4290/4030/4031.

La regla `/analytics` (10 req/min/IP) vive en la tabla `rate-limit-rules`
(se seedea con `serverless rate-limit set --endpoint=/analytics`).
"""

from __future__ import annotations

from typing import Final

from shared.rate_limit.check import check_or_raise

_ENDPOINT: Final[str] = '/analytics'


def guard(*, ip: str | None, country: str | None) -> None:
    """Aplica el rate-limit per-IP del endpoint `/analytics`.

    Args:
        ip: IP del cliente (de `_meta.ip`).
        country: country code ISO-2 (de `_meta.country`) o None.

    Raises:
        IPBlacklistedError, CountryBlockedError, RateLimitExceededError.
    """
    check_or_raise(
        ip=ip or 'unknown',
        endpoint=_ENDPOINT,
        country=country,
        turnstile_validated=False,  # GET autenticado, sin Turnstile
    )
