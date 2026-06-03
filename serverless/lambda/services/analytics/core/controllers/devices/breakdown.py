"""Controller devices/breakdown — distribuciones de device/browser/os."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.devices import BreakdownInput


class Breakdown(AnalyticsControllerBase):
    """Devuelve device_types, browsers (top 20) y os (top 20) del rango."""

    event_model = BreakdownInput
    service_module = 'services.devices_service'
    service_name = 'breakdown'

    def service_kwargs(self, data: BreakdownInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
        }
