"""Controller analytics/overview — 7 KPIs del rango."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.analytics import OverviewInput


class Overview(AnalyticsControllerBase):
    """Devuelve los 7 KPIs agregados del rango."""

    event_model = OverviewInput
    service_module = 'services.analytics_service'
    service_name = 'overview'

    def service_kwargs(self, data: OverviewInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
        }
