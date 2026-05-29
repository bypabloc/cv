"""Modelo Pydantic del Lambda `cv`.

`CvQueryModel` valida los argumentos de cualquier action de `cv`:
- `niche`: opcional, uno de los 5 niches con CV (`CV_NICHES`) o None.
- `locale`: opcional, 'es' o 'en' (default 'es').

El `_meta` lo inyecta el `http_handler` para uniformidad — no se usa en
`cv` (read-only sin rate-limit), pero se acepta para no romper el shape.

Niches: fuente unica en `shared.core.niches` (spec sessions-normalize,
decision 13). `CV_NICHES` excluye `hub` (no tiene CV propio).
"""

from __future__ import annotations

from typing import Literal

from shared.core import BaseModel, Field

from shared.core.niches import CV_NICHES


class CvRequestMeta(BaseModel):
    """Metadata de transporte que inyecta http_handler. Read-only la ignora."""

    ip: str = ''
    country: str | None = None
    user_agent: str | None = None
    bypass_secret: str | None = None
    cloudfront_meta: dict[str, str] = Field(default_factory=dict)
    # Origin header raw del request. Inyectado por http_handler para
    # uniformidad entre Lambdas. cv no lo usa hoy.
    origin: str | None = None
    # Header Authorization que http_handler inyecta SIEMPRE para uniformidad
    # (lo usa el Lambda auth). cv es read-only sin auth; se declara para no
    # romper el extra:forbid del sub-modelo.
    authorization: str | None = None

    model_config = {'extra': 'forbid'}


class CvQueryModel(BaseModel):
    """Argumentos comunes a todas las actions de la operacion `cv`."""

    niche: str | None = None
    locale: Literal['es', 'en'] = 'es'

    meta: CvRequestMeta = Field(
        default_factory=CvRequestMeta, alias='_meta'
    )

    model_config = {'extra': 'forbid', 'populate_by_name': True}

    def normalized_niche(self) -> str | None:
        """Devuelve el niche si es valido (CV_NICHES), sino None."""
        if self.niche is None:
            return None
        return self.niche if self.niche in CV_NICHES else None
