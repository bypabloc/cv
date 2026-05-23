"""Modelo Pydantic del Lambda `cv`.

`CvQueryModel` valida los argumentos de cualquier action de `cv`:
- `niche`: opcional, uno de los 5 niches validos o None.
- `locale`: opcional, 'es' o 'en' (default 'es').

El `_meta` lo inyecta el `http_handler` para uniformidad — no se usa en
`cv` (read-only sin rate-limit), pero se acepta para no romper el shape.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Niches validos del portfolio.
_VALID_NICHES = frozenset(
    {'fintech', 'architect', 'leader', 'vibe', 'generic'}
)


class CvRequestMeta(BaseModel):
    """Metadata de transporte que inyecta http_handler. Read-only la ignora."""

    ip: str = ''
    country: str | None = None
    user_agent: str | None = None
    bypass_secret: str | None = None

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
        """Devuelve el niche si es valido, sino None (sin filtro)."""
        if self.niche is None:
            return None
        return self.niche if self.niche in _VALID_NICHES else None
