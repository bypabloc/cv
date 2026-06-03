"""Modelos Pydantic de la operacion `visits`.

- `ListInput`: listado paginado de visitas crudas (rango + filtros). NO
  cacheado.
- `LandingPagesInput`: ranking de landing pages por visitas (rango +
  limit). Cacheado.
"""

from __future__ import annotations

from models._common import DateRange, RequestMeta
from shared.core.pydantic_types import ConfigDict, Field

_PAGE_SIZE_DEFAULT = 50
_PAGE_SIZE_MAX = 200
_LIMIT_DEFAULT = 10
_LIMIT_MAX = 50


class ListInput(DateRange):
    """GET ?operation=visits&action=list&from=&to&page=&page_size=&...

    Listado paginado de visitas crudas. Hereda el rango de `DateRange` y
    agrega paginacion (page/page_size con limites) + filtros opcionales
    (niche, country). `page_size > 200` lo rechaza el `le` del campo ->
    ValidationError -> 400.
    """

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=_PAGE_SIZE_DEFAULT, ge=1, le=_PAGE_SIZE_MAX)

    niche: str | None = None
    country: str | None = None

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    def offset(self) -> int:
        """OFFSET para el SQL (`LIMIT page_size OFFSET offset`)."""
        return (self.page - 1) * self.page_size


class LandingPagesInput(DateRange):
    """GET ?operation=visits&action=landing-pages&from=&to&limit=

    Ranking de landing pages por numero de visitas. `limit` default 10,
    max 50 (lo rechaza el `le` del campo -> ValidationError -> 400).
    """

    limit: int = Field(default=_LIMIT_DEFAULT, ge=1, le=_LIMIT_MAX)

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
