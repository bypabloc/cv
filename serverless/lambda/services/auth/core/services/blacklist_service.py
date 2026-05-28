"""JWT blacklist service del Lambda `auth`.

Encapsula las operaciones DDB sobre `portfolio-jwt-blacklist-${stage}`:
PutItem (blacklist un jti), GetItem (lookup), Query GSI by_family_id
(devuelve todos los jti de una familia), BatchWriteItem (revoca la
familia entera).

El item shape:
    {
      jti: str (UUID),
      exp: int (unix seconds) -> TTL (AWS borra el item al exp+48h),
      user_id: str,
      reason: str ('rotation' | 'logout' | 'reuse' | 'admin'),
      family_id: str | None  (solo para refresh, alimenta el GSI),
      blacklisted_at: int (unix seconds)
    }
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from shared.aws import get_table


class BlacklistService:
    """Service de DDB jwt-blacklist (PutItem/GetItem/Query/BatchWrite)."""

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
        """Lista todos los jti blacklisted que pertenecen a la familia.

        Usa el GSI `by_family_id` (Projection=KEYS_ONLY).
        """
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
        """Marca toda la familia como revocada.

        En la practica, NO podemos "borrar" tokens fuera de la DB del
        usuario. Lo que hacemos es asegurar que cada jti que llegue de
        esa familia (incluyendo los emitidos in-flight) este en la
        blacklist hasta su `exp`. Implementacion MVP: blacklisteamos
        el `family_id` como un row sentinela (jti == family_id) con
        reason='reuse'; la verificacion del controller hace Query GSI
        ANTES de aceptar un refresh y rechaza si encuentra cualquier
        item con family_id matching.
        """
        item: dict[str, Any] = {
            'jti': str(family_id),
            'family_id': str(family_id),
            'exp': int(exp),
            'user_id': str(user_id),
            'reason': 'reuse',
            'blacklisted_at': int(time.time()),
        }
        self._table().put_item(Item=item)
