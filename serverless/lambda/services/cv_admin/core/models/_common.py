"""Tipos compartidos entre los modelos del Lambda `cv_admin`.

- `_Meta` modela el bloque `_meta` que `http_handler` inyecta en el `data`
  del request (ip, country, user_agent, origin, authorization). Usa
  `populate_by_name=True` con `alias='_meta'` para aceptarlo en entrada
  como `_meta` y leerlo en codigo via `.meta`.
- `SlugStr` valida slugs kebab-case (mismo criterio que los filenames del
  seed YAML).
- `FlexDate` acepta las fechas del shape YAML del seed: `date` nativo (lo
  produce pyyaml) o string `YYYY`, `YYYY-MM` o `YYYY-MM-DD` (lo manda la
  API). `shared.db.repositories.cv_write.coerce_date` normaliza ambas.
- `BiLang` es un bloque bilingue `{es, en}` con al menos un locale.
- `BulletsBlock` son las listas paralelas es/en de bullets (experiencias).
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from shared.core.pydantic_types import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

# Slug kebab-case ASCII: mismo regex del contrato del plan.
SLUG_PATTERN = r'^[a-z0-9]+(-[a-z0-9]+)*$'

SlugStr = Annotated[
    str, Field(pattern=SLUG_PATTERN, min_length=1, max_length=120)
]

# Fecha flexible del seed: date nativo o 'YYYY' / 'YYYY-MM' / 'YYYY-MM-DD'.
FlexDate = date | Annotated[str, Field(pattern=r'^\d{4}(-\d{2}(-\d{2})?)?$')]

# Mapa de prioridades por niche: {<niche-slug>: <peso>}.
PriorityMap = dict[str, int]


class _Meta(BaseModel):
    """Metadata de transporte HTTP inyectada por `http_handler`."""

    ip: str | None = None
    country: str | None = None
    user_agent: str | None = None
    origin: str | None = None
    # Header `Authorization: Bearer <access JWT>`. Lo consume
    # `require_active_user` (TODAS las actions de cv_admin son admin-only).
    authorization: str | None = None
    # Mapa raw de los headers cloudfront-* del request.
    cloudfront_meta: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra='ignore')


class BiLang(BaseModel):
    """Bloque bilingue `{es, en}` — al menos un locale presente."""

    es: str | None = Field(default=None, min_length=1)
    en: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra='forbid')

    @model_validator(mode='after')
    def _at_least_one_locale(self) -> BiLang:
        """Exige al menos un locale (es o en) con valor."""
        if self.es is None and self.en is None:
            msg = 'el bloque bilingue requiere al menos un locale (es/en)'
            raise ValueError(msg)
        return self


class BulletsBlock(BaseModel):
    """Listas paralelas es/en de bullets (responsibilities/achievements)."""

    es: list[str] = Field(default_factory=list)
    en: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')
