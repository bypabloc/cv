"""Helper privado del login con MFA (plan 02).

`issue_terminal_tokens` emite el par access+refresh terminal del login
(con un `family_id` NUEVO uuidv7, segun el lifecycle de JWT: cada login =
nueva familia). Lo comparten `login.start` (con password directo),
`login.verify-password` y `login.verify-totp`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.core.ulid import new_uuidv7


def issue_terminal_tokens(
    *, jwt_svc: Any, user_id: UUID | str
) -> dict[str, Any]:
    """Emite access+refresh con family nuevo. Devuelve el dict de la response."""
    access_token, _ = jwt_svc.issue_access(user_id=user_id)
    family_id = UUID(new_uuidv7())
    refresh_token, _ = jwt_svc.issue_refresh(
        user_id=user_id,
        family_id=family_id,
    )
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 900,
    }
