"""Admin authz guard del Lambda `cv` (operations admin).

`require_admin_user` valida que el email del caller este en la whitelist
SSM (`shared.auth.require_admin`). Si NO es admin, loguea el intento (sin
PII mas alla del user_id) y re-levanta `AdminAuthzError` (404 — oculta la
existencia del endpoint, anti-enumeration). TODAS las actions de las operations admin del cv
son admin-only: escribir el CV y disparar deploys es scope del owner.
"""

from __future__ import annotations

from typing import Any

from settings.config import LogMetricType, logger
from shared.auth.admin import AdminAuthzError, require_admin


def require_admin_user(
    user: Any,
    *,
    ip: str | None = None,
    audit_action: str = 'cv.access',
) -> None:
    """Valida que `user.email` sea admin.

    Levanta `AdminAuthzError` (404 NOT_FOUND, anti-enumeration) si no lo
    es, registrando el intento en el log estructurado.
    """
    try:
        require_admin(user.email)
    except AdminAuthzError:
        logger.warning(
            'cv: acceso denegado (no-admin)',
            extra={
                'metric_type': LogMetricType.CV_ADMIN_ADMIN_DENIED.value,
                'user_id': str(user.id),
                'action': audit_action,
                'ip': ip,
            },
        )
        raise
