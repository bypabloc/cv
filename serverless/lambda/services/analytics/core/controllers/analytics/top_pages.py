"""Controller analytics/top-pages — top page_path por eventos."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.analytics import TopPagesInput


class TopPages(AnalyticsControllerBase):
    """Devuelve el top de page_path por eventos del rango."""

    event_model = TopPagesInput
    service_module = 'services.analytics_service'
    service_name = 'top_pages'

    def service_kwargs(self, data: TopPagesInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'limit': data.limit,
            'niche': data.niche,
        }
