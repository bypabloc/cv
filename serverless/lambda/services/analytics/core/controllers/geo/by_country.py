"""Controller geo/by-country."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.geo import ByCountryInput


class ByCountry(AnalyticsControllerBase):
    """Top paises por sesiones del rango (cacheado)."""

    event_model = ByCountryInput
    service_module = 'services.geo_service'
    service_name = 'by_country'

    def service_kwargs(self, data: ByCountryInput) -> dict[str, Any]:
        """Pasa el rango (date_to EXCLUSIVO) + el limit al service."""
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'limit': data.limit,
        }
