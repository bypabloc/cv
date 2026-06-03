"""Auth guard del Lambda `analytics`.

Envuelve `jwt_service.require_active_user` para los controllers: lee el
header `Authorization` de `_meta.authorization` (lo inyecta http_handler) y
valida que sea un access JWT de un user activo. Sin JWT valido -> 401
(`code 4010`). Es la PRIMERA capa de cada controller (antes del rate-limit),
asi un 401 NO consume slot del rate-limit (AC-23).

NO valida scope admin: cualquier user autenticado lee las metricas
(Decision 1 del plan).
"""

from __future__ import annotations

from services import jwt_service
from settings.config import app_config


def require_auth(*, authorization: str | None) -> None:
    """Valida el access JWT. Levanta ApplicationError(401/403) si falla.

    Args:
        authorization: el header `Authorization` crudo
            (`_meta.authorization`).

    Raises:
        ApplicationError: 401 si falta/invalida el auth; 403 si la cuenta
            esta disabled/locked. http_handler la mapea al HTTP status.
    """
    jwt_service.require_active_user(authorization, app_config=app_config)
