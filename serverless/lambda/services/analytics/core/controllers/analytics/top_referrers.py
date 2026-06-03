"""Controller analytics/top-referrers — top referrers + utm breakdown."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.analytics import TopReferrersInput


class TopReferrers(AnalyticsControllerBase):
    """Devuelve el top de referrers + breakdown de utm del rango."""

    event_model = TopReferrersInput
    service_module = 'services.analytics_service'
    service_name = 'top_referrers'

    def service_kwargs(self, data: TopReferrersInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'limit': data.limit,
        }
