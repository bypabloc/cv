"""
Decision: resultado de check_or_raise (cuando se llama via API alternativa).

En el flujo normal `check_or_raise` levanta excepcion al rechazar; el Decision
TypedDict se usa para auditoria/logging cuando se quiere registrar el resultado
sin levantar.
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class Decision(TypedDict):
    """Resultado del check rate-limit."""

    # True si la request puede continuar
    allowed: bool

    # Razon legible (logged): 'allowed', 'ip_whitelist', 'ip_blacklist',
    # 'country_blocked', 'rate_limit', 'limit_per_window'
    reason: str

    # Si rechazado: cuantos segundos esperar antes de retry
    retry_after_seconds: NotRequired[int]

    # HTTP status code sugerido (200 para allowed, 403/429 para deny)
    status_code: int
