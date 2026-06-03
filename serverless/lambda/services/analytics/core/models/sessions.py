"""Modelos Pydantic de la operacion `sessions`.

- `ListInput`: listado paginado de sesiones (hereda de DateRange +
  paginacion + filtros opcionales device_type/browser).
- `DetailInput`: detalle de UNA sesion (session_id requerido, NO rango).
"""

from __future__ import annotations

from models._common import DateRange, RequestMeta
from shared.core.pydantic_types import BaseModel, ConfigDict, Field

_PAGE_SIZE_DEFAULT = 50
_PAGE_SIZE_MAX = 200


class ListInput(DateRange):
    """GET ?operation=sessions&action=list&from=&to=&page=&page_size=.

    Filtros opcionales: device_type, browser (match exacto). Hereda el
    rango de fechas (from/to, defaults 30d, max 90d) de DateRange y agrega
    paginacion + filtros.
    """

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=_PAGE_SIZE_DEFAULT, ge=1, le=_PAGE_SIZE_MAX)
    device_type: str | None = None
    browser: str | None = None
    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    def offset(self) -> int:
        """OFFSET para el SQL (`LIMIT page_size OFFSET offset`)."""
        return (self.page - 1) * self.page_size


class DetailInput(BaseModel):
    """GET ?operation=sessions&action=detail&session_id=.

    NO hereda DateRange: el detalle es de UNA sesion concreta, sin rango.
    """

    session_id: str = Field(min_length=1)
    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
