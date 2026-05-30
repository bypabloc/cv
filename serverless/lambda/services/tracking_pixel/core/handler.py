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
from shared.aws.warmup import warm_aws_clients
from shared.lambda_kit.event_model import build_event_model
from shared.lambda_kit.http_dispatch import http_handler
from shared.observability.logger import logger
from shared.observability.metrics import metrics

__version__ = '3.2.0'

# Endpoint que el rate-limit usa (mismo literal que el controller track).
_TRACK_ENDPOINT = '/track'

# Clase EventModel ligada al OPERATIONS del Lambda (la construye el kit).
_EVENT_MODEL = build_event_model(OPERATIONS)


def _warm_init() -> None:
    """Precalienta el hot path de EXECUTE en la fase INIT (SnapStart).

    Por que: a 128 MB el EXECUTE recibe ~0.07 vCPU. boto3 construye el
    service model + cada modelo de OPERACION (get_item, query, ...) de
    forma LAZY en la PRIMERA llamada. Si eso cae en EXECUTE, el cold
    tardaba >30s -> timeout 502/504. El INIT tiene CPU sin throttle y
    queda en el SNAPSHOT de SnapStart: warmeando aqui, el EXECUTE solo
    reusa estructuras ya construidas.

    Dos pasos, ambos best-effort (un fallo NUNCA rompe el INIT — ej. sin
    red en un test):
      1. Construye los clientes boto3 (DynamoDB + SQS).
      2. Ejercita el camino de LECTURA del rate-limit con una IP
         sintetica. Son lecturas IDEMPOTENTES (get_ip_rule /
         get_endpoint_rule / get_effective_count): NO incrementan el
         bucket ni escriben nada, pero materializan los modelos de
         operacion get_item/query (+ el get_item de la tabla cache que
         envuelve `@cached`). El INCREMENT real (write) lo hace el
         EXECUTE; su modelo update_item es barato comparado con las
         lecturas. Ver .claude/rules/lambda-config.md.
    """
    warm_aws_clients(dynamodb=True, sqs=True)
    try:
        from shared.rate_limit.buckets import get_effective_count
        from shared.rate_limit.rules import get_endpoint_rule, get_ip_rule

        _synthetic_ip = '0.0.0.0'
        get_ip_rule(_synthetic_ip)
        get_endpoint_rule(_TRACK_ENDPOINT)
        get_effective_count(
            ip=_synthetic_ip, endpoint=_TRACK_ENDPOINT, window_seconds=60,
        )
    except Exception as exc:  # noqa: BLE001 -- best-effort, no rompe INIT
        logger.debug('warm rate-limit reads omitido: %s', type(exc).__name__)


_warm_init()


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
