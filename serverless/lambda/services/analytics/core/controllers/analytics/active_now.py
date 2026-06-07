"""Controller analytics/active-now — sesiones activas (ultimos 5 min)."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.analytics import ActiveNowInput


class ActiveNow(AnalyticsControllerBase):
    """Devuelve el conteo de sesiones activas (sin rango de fechas)."""

    event_model = ActiveNowInput
    service_module = 'services.analytics_service'
    service_name = 'active_now'

    def service_kwargs(self, data: ActiveNowInput) -> dict[str, Any]:
        return {}
