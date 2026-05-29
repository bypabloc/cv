"""Rate-limit service del Lambda `users`.

Wrapper de `shared.rate_limit.check_or_raise` con la signature del dominio.
El rate-limit es per-IP + endpoint (el `endpoint` string es la dimension;
ej. `/users#profile.update`). Las reglas se seedean en la tabla
`rate-limit-rules` (operativo). El service centraliza el call para que los
tests del controller lo mockeen facil.
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
            endpoint: identificador `/users#<operation>.<action>`.
            country: ISO 3166-1 alpha-2 (opcional).

        Raises:
            shared.rate_limit.exceptions.IPBlacklistedError,
            CountryBlockedError, RateLimitExceededError.

        Nota: `turnstile_validated=False` SIEMPRE. Los endpoints de `users`
        son JWT-authed (sin Turnstile); pasar True incrementaria el counter
        de turnstile_tokens del bucket y auto-blacklistearia a un user
        legitimo que haga 3+ requests en 60s (dashboard que carga varios
        endpoints). El rate-limit normal (effective >= limit) igual aplica.
        """
        check_or_raise(
            ip=ip,
            endpoint=endpoint,
            country=country,
            turnstile_validated=False,
        )
