"""Controller visits/list — listado paginado de visitas crudas."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.visits import ListInput


class List(AnalyticsControllerBase):
    """Listado paginado de visitas crudas del rango con filtros opcionales."""

    event_model = ListInput
    service_module = 'services.visits_service'
    service_name = 'list'

    def service_kwargs(self, data: ListInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'page': data.page,
            'page_size': data.page_size,
            'offset': data.offset(),
            'niche': data.niche,
            'country': data.country,
        }
