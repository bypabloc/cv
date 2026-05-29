"""Lambda `users` — endpoint HTTP `POST /users`.

Entrypoint del Lambda. Router delgado que delega TODO el ciclo al
`http_handler` generico de `shared.lambda_kit`. El cliente envia
`operation` y `action` en el body JSON:

    POST /users
    {
      "operation": "profile" | "status" | "admin",
      "action": "get" | "update" | "list-users" | ...,
      "data": { ... }
    }

El `http_handler` extrae `operation`/`action`/`data` del body, inyecta
`data._meta` con la metadata de transporte (IP, country, user-agent,
authorization) y ejecuta el ciclo `preload -> validate -> execute` del
controller resuelto por `OPERATIONS`.

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

from models.event import EVENT_MODEL
from settings.operations import OPERATIONS
from shared.lambda_kit import http_handler
from shared.observability.logger import logger
from shared.observability.metrics import metrics

__version__ = '0.1.0'


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entrypoint Lambda users (POST /users).

    Delega en `http_handler` con CORS echo (dashboard + niches con auth) y
    las 3 metricas CloudWatch (UsersRequestAccepted/Rejected/Error).

    Status de exito: HTTP 200 por default; los controllers piden 204 en
    operaciones sin body (update sin cambios, revoke, disable, delete).
    """
    return http_handler(
        event,
        event_model=EVENT_MODEL,
        cors_origin='echo',
        success_status=200,
        metric_names={
            'submitted': 'UsersRequestAccepted',
            'rejected': 'UsersRequestRejected',
            'error': 'UsersRequestError',
        },
    )


# OPERATIONS se importa para forzar el registro de las operations
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
