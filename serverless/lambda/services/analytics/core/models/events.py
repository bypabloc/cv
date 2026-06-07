"""Modelos Pydantic de la operacion `events`.

- `DistributionInput`: distribucion de eventos por tipo (rango).
- `ListInput`: listado paginado de eventos crudos (rango + filtros).
- `HeatmapInput`: heatmap por dia-de-semana / hora (rango).
"""

from __future__ import annotations

from models._common import DateRange, RequestMeta
from shared.core.pydantic_types import ConfigDict, Field

_PAGE_SIZE_DEFAULT = 50
_PAGE_SIZE_MAX = 200


class DistributionInput(DateRange):
    """GET ?operation=events&action=distribution&from=&to="""

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class ListInput(DateRange):
    """GET ?operation=events&action=list&from=&to&page=&page_size=&...

    Listado paginado de eventos crudos. Hereda el rango de `DateRange` y
    agrega paginacion (page/page_size con limites) + filtros opcionales.
    `page_size > 200` lo rechaza el `le` del campo -> ValidationError -> 400.
    """

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=_PAGE_SIZE_DEFAULT, ge=1, le=_PAGE_SIZE_MAX)

    niche: str | None = None
    event_type: str | None = None
    session_id: str | None = None
    page_path: str | None = None

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    def offset(self) -> int:
        """OFFSET para el SQL (`LIMIT page_size OFFSET offset`)."""
        return (self.page - 1) * self.page_size


class HeatmapInput(DateRange):
    """GET ?operation=events&action=heatmap&from=&to="""

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
