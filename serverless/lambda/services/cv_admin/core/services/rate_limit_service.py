"""Rate-limit service del Lambda `cv_admin`.

Wrapper de `shared.rate_limit.check_or_raise` con la signature del dominio.
El rate-limit es per-IP + endpoint (el `endpoint` string es la dimension;
ej. `/cv-admin#content`, `/cv-admin#publish.dispatch`). Las reglas se
seedean en la tabla `rate-limit-rules` (operativo — ver el README del
Lambda). El service centraliza el call para que los tests del controller
lo mockeen facil.
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
    ) -> None:
        """Aplica el rate-limit per-IP; raises si lo viola.

        Args:
            ip: IP del cliente.
            endpoint: identificador `/cv-admin#<operation>[.<action>]`.
            country: ISO 3166-1 alpha-2 (opcional).

        Raises:
            shared.rate_limit.exceptions.IPBlacklistedError,
            CountryBlockedError, RateLimitExceededError.

        Nota: `turnstile_validated=False` SIEMPRE. Los endpoints de
        `cv_admin` son JWT-authed (sin Turnstile); pasar True
        incrementaria el counter de turnstile_tokens del bucket y
        auto-blacklistearia al admin legitimo que edita varias entidades
        seguidas. El rate-limit normal (effective >= limit) igual aplica.
        """
        check_or_raise(
            ip=ip,
            endpoint=endpoint,
            country=country,
            turnstile_validated=False,
        )
