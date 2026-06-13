"""Lambda `cv` — endpoint HTTP `GET|POST /cv`.

Entrypoint del Lambda. Router delgado que delega TODO el ciclo al
`http_handler` generico de `shared.lambda_kit`. Tres operations:

    GET  /cv?operation=cv&action=get&niche=fintech&locale=es   (publica)
    POST /cv {"operation": "content", "action": "upsert-experience", ...}
    POST /cv {"operation": "content", "action": "get-all"}
    POST /cv {"operation": "publish", "action": "dispatch"}

`content` y `publish` (ex Lambda `cv_admin`, plan d-cv-consolidation) son
admin-only: sus controllers declaran `required_permission = 'admin'` y la
fase Authorize del kit las resuelve con el checker registrado abajo
(access JWT + whitelist SSM admin-emails). La operation `cv` sigue
publica y cacheada; toda la query SQL vive en `shared.db.cv_repository`.

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

# Modulos de modelos CONCRETOS del CV + auth.user (lo usa el permission
# checker: session.get(AuthUser) en require_active_user). Imports
# concretos (NUNCA barrels); cada modulo importa sus FK targets.
import shared.db.models.auth.user
import shared.db.models.cv.cv_entity
import shared.db.models.cv.education
import shared.db.models.cv.experience
import shared.db.models.cv.profile
import shared.db.models.cv.project
import shared.db.models.cv.skill
import shared.db.models.i18n.translation
import shared.db.models.taxonomy.catalog
import shared.db.models.taxonomy.event_type
import shared.db.models.taxonomy.priority  # noqa: F401
from models.event import EVENT_MODEL
from services.permission_checker import check_permission
from shared.db.warmup import warm_db
from shared.lambda_kit.base_controller import set_permission_checker
from shared.lambda_kit.http_dispatch import http_handler
from shared.observability.logger import logger
from shared.observability.metrics import metrics

__version__ = '2.0.0'

# CORS por operation: el GET publico responde '*' (lo consume el prebuild
# de las apps y cualquier agente); las operations admin echoan el Origin
# whitelisteado (el subdominio del admin en CORS_ALLOWED_ORIGINS).
_CORS_BY_OPERATION = {'cv': 'public', '*': 'echo'}

# Checker de permisos del Lambda (fase Authorize del kit): los
# controllers de content/publish declaran required_permission='admin'.
set_permission_checker(check_permission)

# Precalienta engine (NullPool, sin conexion) + configure_mappers de los
# dominios cv/taxonomy/i18n/auth en el INIT. Best-effort (NUNCA rompe el
# INIT). Ver .claude/rules/lambda-config.md.
warm_db()


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entrypoint Lambda cv (GET|POST /cv).

    Delega en `http_handler` con CORS por operation (publico para la
    lectura, echo para content/publish), HTTP 200 en exito y las 3
    metricas CloudWatch (CvQueryOk/Rejected/Error).
    """
    return http_handler(
        event,
        event_model=EVENT_MODEL,
        cors_origin=_CORS_BY_OPERATION,
        success_status=200,
        metric_names={
            'submitted': 'CvQueryOk',
            'rejected': 'CvQueryRejected',
            'error': 'CvQueryError',
        },
    )
