"""Controller analytics/top-niches — top niches por visitas."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.analytics import TopNichesInput


class TopNiches(AnalyticsControllerBase):
    """Devuelve el top de niches por visitas del rango."""

    event_model = TopNichesInput
    service_module = 'services.analytics_service'
    service_name = 'top_niches'

    def service_kwargs(self, data: TopNichesInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'limit': data.limit,
        }
