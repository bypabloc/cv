"""Modelos Pydantic de la operation `status` (plan 03).

3 actions: get (estado + MFA info), list-sessions (sesiones activas),
revoke-session (cierra una sesion que NO sea la actual). Todas requieren
access JWT.
"""

from __future__ import annotations

from uuid import UUID

from shared.core.pydantic_types import BaseModel, ConfigDict, Field

from ._common import _Meta


class StatusGetIn(BaseModel):
    """POST /users operation=status action=get (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class StatusListSessionsIn(BaseModel):
    """POST /users operation=status action=list-sessions (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class StatusRevokeSessionIn(BaseModel):
    """POST /users operation=status action=revoke-session.

    `session_id` es el PK (uuid) de la sesion a cerrar.
    """

    session_id: UUID
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')
