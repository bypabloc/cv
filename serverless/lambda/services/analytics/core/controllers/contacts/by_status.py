"""Controller contacts/by-status — distribucion de contactos por status."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.contacts import ByStatusInput


class ByStatus(AnalyticsControllerBase):
    """Devuelve count + pct por status de contacto en el rango."""

    event_model = ByStatusInput
    service_module = 'services.contacts_service'
    service_name = 'by_status'

    def service_kwargs(self, data: ByStatusInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
        }
