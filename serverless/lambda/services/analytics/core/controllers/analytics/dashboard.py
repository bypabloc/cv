"""Controller analytics/dashboard — las 7 vistas del overview en 1 request."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.analytics import DashboardInput


class Dashboard(AnalyticsControllerBase):
    """Agrega overview/timeseries/top-pages/top-referrers/top-niches/
    active-now/retention del rango en una sola respuesta.
    """

    event_model = DashboardInput
    service_module = 'services.analytics_service'
    service_name = 'dashboard'

    def service_kwargs(self, data: DashboardInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'bucket': data.bucket,
            'limit': data.limit,
        }
