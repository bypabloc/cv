"""Controller events/list — listado paginado de eventos crudos."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.events import ListInput


class List(AnalyticsControllerBase):
    """Listado paginado de eventos crudos del rango con filtros opcionales."""

    event_model = ListInput
    service_module = 'services.events_service'
    service_name = 'list'

    def service_kwargs(self, data: ListInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'page': data.page,
            'page_size': data.page_size,
            'offset': data.offset(),
            'niche': data.niche,
            'event_type': data.event_type,
            'session_id': data.session_id,
            'page_path': data.page_path,
        }
