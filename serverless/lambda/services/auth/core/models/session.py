"""Modelos Pydantic de la operation `session` (refresh + logout).

2 actions:
- `refresh`: el cliente intercambia un refresh JWT por un par
  access+refresh nuevo (rotacion + family detection).
- `logout`: el cliente revoca su access + (opcionalmente) refresh JWT
  — el service blacklistea ambos en DDB.
"""

from __future__ import annotations

from shared.core.pydantic_types import BaseModel, ConfigDict, Field

from ._common import _Meta


class SessionRefreshIn(BaseModel):
    """POST /auth operation=session action=refresh.

    El refresh viaja en el body. El controller verifica typ='refresh',
    chequea blacklist, y si OK -> rota la familia (blacklistea el
    refresh viejo, emite refresh nuevo con el mismo family_id).
    """

    refresh_token: str = Field(..., min_length=20)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class SessionLogoutIn(BaseModel):
    """POST /auth operation=session action=logout.

    `access_token` es obligatorio (lo necesitamos para identificar al
    user y blacklistear su jti). `refresh_token` es opcional: si llega,
    el service blacklistea la familia completa (Query GSI + BatchWrite).
    """

    access_token: str = Field(..., min_length=20)
    refresh_token: str | None = Field(default=None, min_length=20)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
