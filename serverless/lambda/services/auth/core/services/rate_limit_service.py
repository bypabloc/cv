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
        brought_turnstile_token: bool = False,
    ) -> None:
        """Aplica el rate-limit; raises si IP/country/window-rule lo violan.

        Args:
            ip: IP del cliente (CF-Connecting-IP).
            endpoint: path identificador (ej.
                `/auth#register.start`, `/auth#login.verify-code`).
            country: ISO 3166-1 alpha-2 (de CF-IPCountry, opcional).
            turnstile_validated: si la request usa el limite alto del
                rate-limit (verify-*/mfa/session lo pasan True). NO alimenta
                la auto-blacklist.
            brought_turnstile_token: True solo en login.start/register.start,
                donde el usuario ADJUNTA un CAPTCHA real. Unico flag que
                alimenta la auto-blacklist (bot detection).

        Raises:
            shared.rate_limit.exceptions.IPBlacklistedError,
            CountryBlockedError, RateLimitExceededError.
        """
        brought_captcha = brought_turnstile_token
        check_or_raise(
            ip=ip,
            endpoint=endpoint,
            country=country,
            turnstile_validated=turnstile_validated,
            brought_turnstile_token=brought_captcha,
        )
