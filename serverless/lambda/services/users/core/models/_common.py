"""Tipos compartidos entre los modelos del Lambda `users`.

`_Meta` modela el bloque `_meta` que `http_handler` inyecta en el `data`
del request (ip, country, user_agent, origin, authorization extraidos de
los headers de API Gateway). Usa `populate_by_name=True` con
`alias='_meta'` para aceptarlo en entrada como `_meta` y leerlo en codigo
via `.meta`. `extra='ignore'` tolera campos del `_meta` que el modelo no
declara (cloudfront_meta, bypass_secret).
"""

from __future__ import annotations

from shared.core.pydantic_types import BaseModel, ConfigDict, Field


class _Meta(BaseModel):
    """Metadata de transporte HTTP inyectada por `http_handler`."""

    ip: str | None = None
    country: str | None = None
    user_agent: str | None = None
    origin: str | None = None
    # Header `Authorization: Bearer <access JWT>`. Lo consume
    # `require_active_user` en los endpoints autenticados.
    authorization: str | None = None
    # Mapa raw de los headers cloudfront-* del request.
    cloudfront_meta: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra='ignore')
