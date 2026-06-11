"""Permission checker del Lambda `cv` (operations admin content/publish).

Implementa el contrato `PermissionChecker` de `shared.lambda_kit` y se
registra UNA vez en el cold start del handler con
`set_permission_checker(check_permission)`. La fase Authorize de
`BaseController.run()` lo invoca para todo controller que declara
`required_permission` (los de content/publish declaran 'admin').

Para `'admin'` compone los dos guards del dominio:

1. `require_active_user` — access JWT valido (firma HS256 + blacklist
   DDB + status del user en Neon) -> 401/403.
2. `require_admin_user` — whitelist SSM admin-emails -> 404 NOT_FOUND
   (anti-enumeration).

Devuelve el `AuthUser` (queda en `controller.permission_subject`).
"""

from __future__ import annotations

from typing import Any

from services.admin_guard import require_admin_user
from services.jwt_service import require_active_user
from settings.config import app_config
from shared.core.exceptions import ApplicationError


def check_permission(
    permission: str,
    meta: dict[str, Any],
    *,
    action: str,
) -> Any:
    """Resuelve el permiso declarado por un controller del Lambda `cv`.

    Args:
        permission: permiso requerido. Hoy solo `'admin'` es valido.
        meta: `_meta` crudo del event (authorization, ip, country, ...).
        action: nombre de la clase del controller (para el log de denial).

    Returns:
        El `AuthUser` autenticado y autorizado.

    Raises:
        ApplicationError: 401/403 (JWT/estado del user), 404 (no-admin,
            anti-enumeration) o 500 si el permiso declarado no existe
            (bug de configuracion, no del caller).
    """
    if permission != 'admin':
        raise ApplicationError(
            f'permiso desconocido: {permission}',
            code='CONFIGURATION_ERROR',
            status_code=500,
        )

    user = require_active_user(
        meta.get('authorization'), app_config=app_config,
    )
    require_admin_user(
        user, ip=meta.get('ip'), audit_action=f'cv.{action}',
    )
    return user
