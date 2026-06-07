"""Controller sessions/list — listado paginado de sesiones."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.sessions import ListInput


class List(AnalyticsControllerBase):
    """Listado paginado de sesiones del rango, con filtros opcionales."""

    event_model = ListInput
    service_module = 'services.sessions_service'
    service_name = 'list'

    def service_kwargs(self, data: ListInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'page': data.page,
            'page_size': data.page_size,
            'offset': data.offset(),
            'device_type': data.device_type,
            'browser': data.browser,
        }
