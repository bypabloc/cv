"""Controller funnel/conversion — embudo session -> visit -> contact."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.funnel import ConversionInput


class Conversion(AnalyticsControllerBase):
    """Devuelve sessions/visits/contacts + rates de conversion del rango."""

    event_model = ConversionInput
    service_module = 'services.funnel_service'
    service_name = 'conversion'

    def service_kwargs(self, data: ConversionInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
        }
