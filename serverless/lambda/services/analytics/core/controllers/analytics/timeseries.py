"""Controller analytics/timeseries — serie temporal de eventos."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.analytics import TimeseriesInput


class Timeseries(AnalyticsControllerBase):
    """Devuelve la serie temporal de eventos por bucket (day|hour|week)."""

    event_model = TimeseriesInput
    service_module = 'services.analytics_service'
    service_name = 'timeseries'

    def service_kwargs(self, data: TimeseriesInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'bucket': data.bucket,
            'niche': data.niche,
            'event_type': data.event_type,
        }
