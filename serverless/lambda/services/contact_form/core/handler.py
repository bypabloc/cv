"""Lambda `contact_form` — endpoint HTTP `POST /contact`.

Entrypoint del Lambda. Router delgado que delega TODO el ciclo al
`http_handler` generico de `shared.lambda_kit`. El cliente envia
`operation` y `action` en el body JSON junto con los campos del form:

    POST /contact
    {
      "operation": "contact",
      "action": "create",
      "name": "...", "email": "...", "message": "...",
      "cf_token": "...", ...
    }

El `http_handler` extrae `operation`/`action`/`data` del body, inyecta
`data._meta` con la metadata de transporte (IP, country, user-agent,
bypass-token) y ejecuta el ciclo `preload -> validate -> execute` del
controller `contact/create`. Toda la logica de negocio vive en
`services/contact_service.py`: escribe el contacto INLINE a Neon (sin
SQS) y notifica al owner invocando `send_email` async. Responde HTTP 201.

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

import shared.db.models.visitor.contact
import shared.db.models.visitor.session
import shared.db.models.visitor.session_visit
import shared.db.models.visitor.tracking  # noqa: F401
from settings.operations import OPERATIONS
from shared.db.warmup import warm_db
from shared.lambda_kit.event_model import build_event_model
from shared.lambda_kit.http_dispatch import http_handler
from shared.observability.logger import logger
from shared.observability.metrics import metrics

__version__ = '4.0.0'

# Clase EventModel ligada al OPERATIONS del Lambda (la construye el kit).
_EVENT_MODEL = build_event_model(OPERATIONS)

# SnapStart: precalienta engine (NullPool) + configure_mappers del dominio
# visitor en el INIT -> queda en el snapshot. Best-effort.
warm_db()


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entrypoint Lambda contact_form (POST /contact).

    Delega en `http_handler` con CORS echo (form del visitante) y las 3
    metricas CloudWatch (Submitted/Rejected/Error).

    Status de exito: HTTP 201 Created — el contacto se persiste INLINE a
    Neon en el request (el email al owner se delega a `send_email` async,
    fire-and-forget). Sin SQS, sin ASYNC_MODE.
    """
    return http_handler(
        event,
        event_model=_EVENT_MODEL,
        cors_origin='echo',
        success_status=201,
        metric_names={
            'submitted': 'ContactFormSubmitted',
            'rejected': 'ContactFormRejected',
            'error': 'ContactFormError',
        },
    )


# OPERATIONS se importa para forzar el registro de la operacion `contact`
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
