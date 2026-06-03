"""Lambda `analytics` — endpoint HTTP `GET /analytics`.

Entrypoint del Lambda. Router delgado que delega TODO el ciclo al
`http_handler` generico de `shared.lambda_kit`. El cliente envia
`operation` y `action` como query params del GET, y el access JWT en el
header `Authorization: Bearer <token>`:

    GET /analytics?operation=analytics&action=overview&from=...&to=...
    GET /analytics?operation=sessions&action=detail&session_id=...

El `http_handler` extrae `operation`/`action`/`data` del query string,
inyecta `data._meta` (que incluye `authorization`, `ip`, `country`, ...) y
ejecuta el ciclo del controller `<operation>/<action>`. Cada controller
valida el JWT (auth_guard), aplica rate-limit y llama a su service.

Observabilidad: SOLO logs estructurados + metrics (NO X-Ray; ver
.claude/rules/lambda-config.md). El Handler de la funcion AWS es
`core.handler.lambda_handler`.
"""

from __future__ import annotations

import os
import sys

# El handler vive dentro de core/. Agregamos core/ al sys.path para que
# los imports absolutos (models., services., controllers., settings.,
# shared.) resuelvan en AWS y en invoke local.
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any

# Registrar los modulos de modelos CONCRETOS que tocan las queries en el
# INIT -> warm_db() los captura en el snapshot de SnapStart (FK resolved,
# mappers configurados). Imports concretos (NUNCA barrels): solo el closure
# de visitor + taxonomy (los dominios que las queries usan).
import shared.db.models.taxonomy.event_type
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

__version__ = '1.0.0'

# Clase EventModel ligada al OPERATIONS del Lambda (la construye el kit).
_EVENT_MODEL = build_event_model(OPERATIONS)

# SnapStart: precalienta engine (NullPool, sin conexion) + configure_mappers
# de los dominios visitor/taxonomy en el INIT -> queda en el snapshot.
# Best-effort (NUNCA rompe el INIT).
warm_db()


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entrypoint Lambda analytics (GET /analytics).

    Delega en `http_handler` con CORS `echo` (refleja el Origin del admin si
    esta en CORS_ALLOWED_ORIGINS — NUNCA '*'), HTTP 200 en exito y las 3
    metricas CloudWatch.
    """
    return http_handler(
        event,
        event_model=_EVENT_MODEL,
        cors_origin='echo',
        success_status=200,
        metric_names={
            'submitted': 'AnalyticsQueryOk',
            'rejected': 'AnalyticsQueryRejected',
            'error': 'AnalyticsQueryError',
        },
    )


# OPERATIONS se importa para forzar el registro de las operaciones
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
