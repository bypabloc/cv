"""Challenge service: CRUD de la tabla DDB `webauthn-challenges`.

Guarda el `state` del ceremony WebAuthn (dict JSON de fido2) entre el
`*-options` y el `*-verify`, con TTL=expires_at (now + 5 min). Single-use:
`get_and_consume` borra el row tras leerlo (un challenge no se reutiliza).
"""

from __future__ import annotations

import json
import time
from typing import Any
from uuid import UUID

from shared.aws import get_table

_TTL_SECONDS = 300


class ChallengeService:
    """PutItem + GetItem/DeleteItem sobre `portfolio-webauthn-challenges`."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def _table(self) -> Any:
        return get_table(
            self.app_config.webauthn_challenges_table_name,  # type: ignore[attr-defined]
        )

    def put(
        self,
        *,
        challenge_id: UUID | str,
        user_id: UUID | str,
        kind: str,
        state: dict[str, Any],
        ttl_seconds: int = _TTL_SECONDS,
    ) -> None:
        """Persiste el challenge con TTL (now + ttl_seconds)."""
        now = int(time.time())
        self._table().put_item(
            Item={
                'challenge_id': str(challenge_id),
                'user_id': str(user_id),
                'kind': kind,
                'state': json.dumps(state),
                'created_at': now,
                'expires_at': now + ttl_seconds,
            },
        )

    def get_and_consume(
        self,
        *,
        challenge_id: UUID | str,
    ) -> dict[str, Any] | None:
        """Lee + borra el challenge (single-use). None si no existe/expiro."""
        key = {'challenge_id': str(challenge_id)}
        resp = self._table().get_item(Key=key)
        item = resp.get('Item')
        if item is None:
            return None
        self._table().delete_item(Key=key)
        return {
            'user_id': item['user_id'],
            'kind': item['kind'],
            'state': json.loads(item['state']),
        }
