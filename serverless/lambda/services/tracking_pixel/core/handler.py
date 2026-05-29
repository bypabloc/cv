"""Lambda `tracking_pixel` — endpoint HTTP `POST /track`.

Entrypoint del Lambda. Router delgado que delega TODO el ciclo al
`http_handler` generico de `shared.lambda_kit`. El cliente envia
`operation` y `action` en el body JSON junto con el evento de tracking:

    POST /track
    {
      "operation": "tracking",
      "action": "track",
      "session_id": "...", "event_type": "...", "page_url": "...", ...
    }

El `http_handler` extrae `operation`/`action`/`data` del body, inyecta
`data._meta` con la metadata de transporte (IP, country, user-agent) y
ejecuta el ciclo del controller `tracking/track`. Toda la logica de
negocio sigue en `services/`; el comportamiento observable (HTTP 204
fire-and-forget, mismo CORS publico para sendBeacon, mismas metricas)
es IDENTICO al handler hardcodeado que reemplaza.

El Handler de la funcion AWS es `core.handler.lambda_handler`.
"""

from __future__ import annotations

import os
import sys

# El handler vive dentro de core/. Agregamos core/ al sys.path para que
# los imports absolutos (models., services., settings., shared.)
# resuelvan en AWS y en invoke local. shared/ se vendoriza en core/shared/.
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any

from settings.config import AppConfig
from settings.operations import OPERATIONS
from shared.lambda_kit.event_model import build_event_model
from shared.lambda_kit.http_dispatch import http_handler
from shared.observability.logger import logger
from shared.observability.metrics import metrics

__version__ = '3.0.0'

# Clase EventModel ligada al OPERATIONS del Lambda (la construye el kit).
_EVENT_MODEL = build_event_model(OPERATIONS)


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entrypoint Lambda tracking_pixel (POST /track).

    Delega en `http_handler` con CORS publico (`*`, exigido por
    navigator.sendBeacon en modo ping). El status code de exito depende
    del feature flag `AppConfig.async_mode`:

      - True  -> HTTP 202 (Accepted; el worker persistira async).
      - False -> HTTP 204 (fire-and-forget legacy; sync write a Neon).

    Las 3 metricas CloudWatch (Received/Rejected/Error) son las mismas
    en ambos modos.
    """
    return http_handler(
        event,
        event_model=_EVENT_MODEL,
        cors_origin='public',
        success_status=202 if AppConfig.async_mode else 204,
        metric_names={
            'submitted': 'TrackingEventReceived',
            'rejected': 'TrackingEventRejected',
            'error': 'TrackingEventError',
        },
    )


# OPERATIONS se importa para forzar el registro de la operacion
# `tracking` (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
