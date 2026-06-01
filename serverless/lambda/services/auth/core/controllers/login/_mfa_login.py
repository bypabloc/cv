"""Helper privado del login con MFA (plan 02 + plan 03).

`issue_terminal_tokens` emite el par access+refresh terminal del login
(con un `family_id` NUEVO uuidv7, segun el lifecycle de JWT: cada login =
nueva familia). Lo comparten `login.start` (con password directo),
`login.verify-password` y `login.verify-totp`.

Plan 03: el access lleva el `family_id` de la sesion (para que el Lambda
`users` identifique la sesion en curso) y, si se pasa `app_config`, se
registra la sesion en `auth_user_sessions` via SessionTrackingService
(best-effort).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from services.session_tracking_service import SessionTrackingService
from shared.core.ulid import new_uuidv7


def issue_terminal_tokens(
    *,
    jwt_svc: Any,
    user_id: UUID | str,
    app_config: Any = None,
    ip: str | None = None,
    country: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    """Emite access+refresh con family nuevo. Devuelve el dict de la response.

    Si `app_config` se pasa, ademas registra la sesion en
    `auth_user_sessions` (best-effort). El `family_id` se genera ANTES de
    emitir el access para embeberlo en sus claims (plan 03).
    """
    family_id = UUID(new_uuidv7())
    access_token, _ = jwt_svc.issue_access(
        user_id=user_id, family_id=family_id,
    )
    refresh_token, _ = jwt_svc.issue_refresh(
        user_id=user_id,
        family_id=family_id,
    )
    if app_config is not None:
        SessionTrackingService(app_config).on_session_created(
            user_id=user_id,
            family_id=family_id,
            ip=ip,
            country=country,
            user_agent=user_agent,
        )
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 900,
    }
