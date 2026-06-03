"""Controller contacts/list — listado paginado de contactos crudos (PII)."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.contacts import ListInput


class List(AnalyticsControllerBase):
    """Listado paginado de contactos del rango con filtros status/niche."""

    event_model = ListInput
    service_module = 'services.contacts_service'
    service_name = 'list'

    def service_kwargs(self, data: ListInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'page': data.page,
            'page_size': data.page_size,
            'offset': data.offset(),
            'status': data.status,
            'niche': data.niche,
        }
