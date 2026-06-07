"""Modelos Pydantic de la operacion `contacts`.

- `ListInput`: listado paginado de contactos crudos (rango + filtros
  status/niche + paginacion). Contiene PII, NO se cachea.
- `ByStatusInput`: distribucion de contactos por status (rango, cacheada).
"""

from __future__ import annotations

from models._common import DateRange, RequestMeta
from shared.core.pydantic_types import ConfigDict, Field

_PAGE_SIZE_DEFAULT = 50
_PAGE_SIZE_MAX = 200


class ListInput(DateRange):
    """GET ?operation=contacts&action=list&from=&to&page=&page_size&...

    Listado paginado de contactos crudos (PII, NO cacheado). Hereda el rango
    de `DateRange` y agrega paginacion (page/page_size con limites) + filtros
    opcionales status/niche. `page_size > 200` lo rechaza el `le` del campo
    -> ValidationError -> 400.
    """

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=_PAGE_SIZE_DEFAULT, ge=1, le=_PAGE_SIZE_MAX)

    status: str | None = None
    niche: str | None = None

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    def offset(self) -> int:
        """OFFSET para el SQL (`LIMIT page_size OFFSET offset`)."""
        return (self.page - 1) * self.page_size


class ByStatusInput(DateRange):
    """GET ?operation=contacts&action=by-status&from=&to="""

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
