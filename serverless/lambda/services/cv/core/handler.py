"""Lambda `cv` — endpoint HTTP `GET /cv`.

Entrypoint del Lambda. Router delgado que delega TODO el ciclo al
`http_handler` generico de `shared.lambda_kit`. El cliente envia
`operation` y `action` como query params del GET:

    GET /cv?operation=cv&action=get&niche=fintech&locale=es
    GET /cv?operation=cv&action=experiences&niche=fintech
    GET /cv?operation=cv&action=profile&locale=es

El `http_handler` extrae `operation`/`action`/`data` del query string,
inyecta `data._meta` (read-only no lo usa) y ejecuta el ciclo del
controller `cv/<action>`. Toda la query SQL vive en
`shared.db.cv_repository`; el controller solo orquesta + normaliza.

El Handler de la funcion AWS es `core.handler.lambda_handler`.
"""

from __future__ import annotations

import os
import sys

# El handler vive dentro de core/. Agregamos core/ al sys.path para que
# los imports absolutos (models., services., settings., shared.)
# resuelvan en AWS y en invoke local.
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any

import shared.db.models.cv
import shared.db.models.i18n
import shared.db.models.taxonomy  # noqa: F401
from settings.operations import OPERATIONS
from shared.db.warmup import warm_db
from shared.lambda_kit.event_model import build_event_model
from shared.lambda_kit.http_dispatch import http_handler
from shared.observability.logger import logger
from shared.observability.metrics import metrics

__version__ = '1.0.0'

# Clase EventModel ligada al OPERATIONS del Lambda (la construye el kit).
_EVENT_MODEL = build_event_model(OPERATIONS)

# SnapStart: precalienta engine (NullPool) + configure_mappers de los
# dominios del CV en el INIT -> queda en el snapshot. Best-effort.
warm_db()


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entrypoint Lambda cv (GET /cv).

    Delega en `http_handler` con CORS publico (`*`, el API lo consume el
    prebuild de las apps sin credenciales), HTTP 200 en exito y las 3
    metricas CloudWatch (CvQueryOk/Rejected/Error).
    """
    return http_handler(
        event,
        event_model=_EVENT_MODEL,
        cors_origin='public',
        success_status=200,
        metric_names={
            'submitted': 'CvQueryOk',
            'rejected': 'CvQueryRejected',
            'error': 'CvQueryError',
        },
    )


# OPERATIONS se importa para forzar el registro de la operacion `cv`
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
