"""JWT blacklist service del Lambda `users`.

Mismo shape que el del Lambda `auth` (los Lambdas son autonomos en el
artefacto, asi que el codigo NO se comparte entre `services/`; la libreria
comun solo vive en `shared/`). Encapsula las operaciones DDB sobre
`portfolio-jwt-blacklist-${stage}`: PutItem (blacklist un jti), GetItem
(lookup), Query GSI by_family_id, y el sentinela de revocacion de familia.

El Lambda `users` blacklistea cuando: revoke-session (la family de la
sesion), force-logout (todas las families del target), delete-account
(todas las families del propio user).

Item shape:
    {jti, exp (TTL), user_id, reason, family_id?, blacklisted_at}
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from shared.aws.dynamodb import get_table


class BlacklistService:
    """Service de DDB jwt-blacklist (PutItem/GetItem/Query)."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def _table(self) -> Any:
        """Resuelve el Resource Table en lazy mode (no en cold start)."""
        table_name = self.app_config.jwt_blacklist_table_name  # type: ignore[attr-defined]
        return get_table(table_name)

    def put(
        self,
        *,
        jti: UUID | str,
        exp: int,
        user_id: UUID | str,
        reason: str,
        family_id: UUID | str | None = None,
    ) -> None:
        """Inserta un jti en la blacklist con TTL=exp."""
        item: dict[str, Any] = {
            'jti': str(jti),
            'exp': int(exp),
            'user_id': str(user_id),
            'reason': reason,
            'blacklisted_at': int(time.time()),
        }
        if family_id is not None:
            item['family_id'] = str(family_id)
        self._table().put_item(Item=item)

    def is_blacklisted(self, *, jti: UUID | str) -> bool:
        """Devuelve True si el jti esta en la blacklist."""
        resp = self._table().get_item(
            Key={'jti': str(jti)},
            ConsistentRead=False,
        )
        return resp.get('Item') is not None

    def query_family(self, *, family_id: UUID | str) -> list[str]:
        """Lista los jti blacklisted de una familia (GSI by_family_id)."""
        resp = self._table().query(
            IndexName='by_family_id',
            KeyConditionExpression='family_id = :fid',
            ExpressionAttributeValues={':fid': str(family_id)},
        )
        return [str(item['jti']) for item in resp.get('Items', [])]

    def revoke_family(
        self,
        *,
        family_id: UUID | str,
        user_id: UUID | str,
        exp: int,
    ) -> None:
        """Marca toda la familia como revocada (sentinela jti==family_id).

        El verify de `session.refresh` (Lambda auth) hace Query GSI ANTES
        de aceptar un refresh y rechaza si encuentra cualquier item con
        ese family_id. TTL = exp del refresh para auto-limpieza.
        """
        item: dict[str, Any] = {
            'jti': str(family_id),
            'family_id': str(family_id),
            'exp': int(exp),
            'user_id': str(user_id),
            'reason': 'revoke',
            'blacklisted_at': int(time.time()),
        }
        self._table().put_item(Item=item)
