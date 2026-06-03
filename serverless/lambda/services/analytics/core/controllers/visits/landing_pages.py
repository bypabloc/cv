"""Controller visits/landing-pages — ranking de landing pages por visitas."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.visits import LandingPagesInput


class LandingPages(AnalyticsControllerBase):
    """Ranking de landing pages por numero de visitas en el rango."""

    event_model = LandingPagesInput
    service_module = 'services.visits_service'
    service_name = 'landing_pages'

    def service_kwargs(self, data: LandingPagesInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
            'limit': data.limit,
        }
