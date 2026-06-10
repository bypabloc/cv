"""Lambda `cv_admin` — endpoint HTTP `POST /cv-admin`.

Entrypoint del Lambda. Router delgado que delega TODO el ciclo al
`http_handler` generico de `shared.lambda_kit`. El cliente envia
`operation` y `action` en el body JSON:

    POST /cv-admin
    {
      "operation": "content" | "publish",
      "action": "upsert-experience" | "delete-project" | "dispatch" | ...,
      "data": { ... }
    }

El `http_handler` extrae `operation`/`action`/`data` del body, inyecta
`data._meta` con la metadata de transporte (IP, country, user-agent,
authorization) y ejecuta el ciclo `preload -> validate -> execute` del
controller resuelto por `OPERATIONS`. TODAS las actions son admin-only
(access JWT + whitelist SSM admin-emails).

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

# Registrar los modulos de modelos CONCRETOS que toca la escritura del CV
# (cv_* + taxonomy + i18n) y el auth (require_active_user) en el INIT.
# Imports concretos (NUNCA barrels); cada modulo importa sus FK targets.
import shared.db.models.auth.user
import shared.db.models.cv.cv_entity
import shared.db.models.cv.education
import shared.db.models.cv.experience
import shared.db.models.cv.profile
import shared.db.models.cv.project
import shared.db.models.cv.skill
import shared.db.models.i18n.translation
import shared.db.models.taxonomy.catalog
import shared.db.models.taxonomy.priority  # noqa: F401
from models.event import EVENT_MODEL
from settings.operations import OPERATIONS
from shared.db.warmup import warm_db
from shared.lambda_kit.http_dispatch import http_handler
from shared.observability.logger import logger
from shared.observability.metrics import metrics

__version__ = '0.1.0'

# Precalienta engine (NullPool, sin conexion) + configure_mappers de los
# dominios cv/taxonomy/i18n/auth en el INIT. Best-effort (NUNCA rompe el
# INIT). Ver .claude/rules/lambda-config.md.
warm_db()


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entrypoint Lambda cv_admin (POST /cv-admin).

    Delega en `http_handler` con CORS echo (solo los origins del admin en
    CORS_ALLOWED_ORIGINS) y las 3 metricas CloudWatch
    (CvAdminRequestAccepted/Rejected/Error).
    """
    return http_handler(
        event,
        event_model=EVENT_MODEL,
        cors_origin='echo',
        success_status=200,
        metric_names={
            'submitted': 'CvAdminRequestAccepted',
            'rejected': 'CvAdminRequestRejected',
            'error': 'CvAdminRequestError',
        },
    )


# OPERATIONS se importa para forzar el registro de las operations
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
