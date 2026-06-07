"""Controller analytics/retention — nuevos vs recurrentes del rango."""

from __future__ import annotations

from typing import Any

from controllers._base import AnalyticsControllerBase
from models.analytics import RetentionInput


class Retention(AnalyticsControllerBase):
    """Devuelve visitantes nuevos vs recurrentes + returning_rate."""

    event_model = RetentionInput
    service_module = 'services.analytics_service'
    service_name = 'retention'

    def service_kwargs(self, data: RetentionInput) -> dict[str, Any]:
        return {
            'date_from': data.date_from,
            'date_to': data.date_to_exclusive(),
        }
