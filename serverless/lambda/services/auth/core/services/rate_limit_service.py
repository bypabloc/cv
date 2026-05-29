"""Rate-limit service del Lambda `auth`.

Wrapper de `shared.rate_limit.check_or_raise` con la signature del
dominio (los controllers solo pasan `ip`, `endpoint` y opcionalmente
`country`). El service centraliza el call para que los tests del
controller puedan mockearlo facil.
"""

from __future__ import annotations

from shared.rate_limit.check import check_or_raise


class RateLimitService:
    """Wrapper del rate-limit check (sliding window weighted)."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def check_or_raise(
        self,
        *,
        ip: str,
        endpoint: str,
        country: str | None = None,
        turnstile_validated: bool = False,
    ) -> None:
        """Aplica el rate-limit; raises si IP/country/window-rule lo violan.

        Args:
            ip: IP del cliente (CF-Connecting-IP).
            endpoint: path identificador (ej.
                `/auth#register.start`, `/auth#login.verify-code`).
            country: ISO 3166-1 alpha-2 (de CF-IPCountry, opcional).
            turnstile_validated: si la request paso Turnstile.

        Raises:
            shared.rate_limit.exceptions.IPBlacklistedError,
            CountryBlockedError, RateLimitExceededError.
        """
        check_or_raise(
            ip=ip,
            endpoint=endpoint,
            country=country,
            turnstile_validated=turnstile_validated,
        )
