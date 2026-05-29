"""Tipos compartidos entre los modelos del Lambda `auth`.

`Niche` es una lista cerrada con los 6 niches del portfolio: cualquier
otro valor en el payload del cliente -> `ValidationError` 400. Evita
que un atacante meta strings arbitrarios (incluyendo HTML/script) en
el audit log o en templates de email del worker.

`_Meta` modela el bloque `_meta` que `http_handler` inyecta al `data`
del request (ip, country, user_agent, bypass_secret, origin extraidos
de los headers de API Gateway). Usa `populate_by_name=True` con
`alias='_meta'` para que se acepte tanto en entrada como `_meta` como
en codigo via `.meta`.
"""

from __future__ import annotations

from typing import Literal

from shared.core.pydantic_types import BaseModel, ConfigDict, Field

# 6 niches publicos del portfolio. Cualquier otro valor en payload ->
# ValidationError 400 (defensa contra strings arbitrarios en audit /
# emails).
Niche = Literal['generic', 'hub', 'fintech', 'architect', 'leader', 'vibe']


class _Meta(BaseModel):
    """Metadata de transporte HTTP inyectada por `http_handler`.

    `http_handler` la inyecta en `data['_meta']` desde los headers de
    API Gateway (CF-Connecting-IP, CF-IPCountry, User-Agent,
    X-Turnstile-Bypass-Secret, Origin). El service NO la conoce: solo
    los controllers la usan para rate-limit + Turnstile + audit.
    """

    ip: str | None = None
    country: str | None = None
    user_agent: str | None = None
    bypass_secret: str | None = None
    origin: str | None = None
    # Header `Authorization: Bearer <access JWT>` inyectado por
    # `http_handler`. Lo consume `require_active_user` en los endpoints
    # autenticados (mfa.*, webauthn.*).
    authorization: str | None = None
    # Mapa raw de los headers cloudfront-* del request (Edge-Optimized
    # API GW los expone). Mismo patron que contact_form para futuras
    # decisiones de geolocation en el worker.
    cloudfront_meta: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra='ignore')
