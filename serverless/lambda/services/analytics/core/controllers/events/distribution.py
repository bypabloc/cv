"""Controller events/distribution — distribucion de eventos por tipo."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.events import DistributionInput


class Distribution(AnalyticsControllerBase):
    """Devuelve count + pct por tipo de evento en el rango."""

    event_model = DistributionInput
    service_module = 'services.events_service'
    service_name = 'distribution'

    def service_kwargs(self, data: DistributionInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
        }
