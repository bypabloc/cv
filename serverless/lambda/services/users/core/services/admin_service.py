"""Admin authz helper del Lambda `users`.

`require_admin_user` valida que el email del caller este en la whitelist
SSM (`shared.auth.require_admin`). Si NO es admin, registra el intento
fallido en `auth_user_admin_actions` (defensa contra probing del scope
admin) y re-levanta `AdminAuthzError` (404 — oculta la existencia del
endpoint, AC-11). Si es admin, NO escribe nada extra: la operacion
concreta (disable/enable/...) registra su propio audit row.
"""

from __future__ import annotations

from typing import Any

from settings.config import app_config
from shared.auth import AdminAuthzError, require_admin

from .audit_admin_service import AuditAdminService


def require_admin_user(
    user: Any,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
    audit_action: str = 'admin.access',
) -> None:
    """Valida que `user.email` sea admin. Levanta `AdminAuthzError` (404)
    si no lo es, registrando el intento fallido."""
    try:
        require_admin(user.email)
    except AdminAuthzError:
        AuditAdminService(app_config).log_attempt(
            admin_user_id=user.id,
            action=audit_action,
            success=False,
            ip=ip,
            user_agent=user_agent,
        )
        raise
