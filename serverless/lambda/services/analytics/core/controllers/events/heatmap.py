"""Controller events/heatmap — heatmap por dia-de-semana / hora."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.events import HeatmapInput


class Heatmap(AnalyticsControllerBase):
    """Devuelve count por (dia-de-semana ISO, hora) en el rango."""

    event_model = HeatmapInput
    service_module = 'services.events_service'
    service_name = 'heatmap'

    def service_kwargs(self, data: HeatmapInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
        }
