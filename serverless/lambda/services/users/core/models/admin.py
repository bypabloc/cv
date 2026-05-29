"""Modelos Pydantic de la operation `admin` (plan 03).

7 actions: list-users, get-user, disable-user, enable-user, force-logout,
delete-user, list-admin-actions. Todas requieren access JWT + que el email
del caller este en la whitelist SSM (`require_admin_user`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from shared.core import BaseModel, ConfigDict, Field, model_validator

from ._common import _Meta


class AdminListUsersIn(BaseModel):
    """POST /users operation=admin action=list-users (paginado)."""

    cursor: UUID | None = None
    page_size: int = Field(default=50, ge=1, le=200)
    status_filter: Literal['pending', 'active', 'disabled', 'locked'] | None = (
        None
    )
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class AdminGetUserIn(BaseModel):
    """POST /users operation=admin action=get-user."""

    user_id: UUID
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class AdminDisableUserIn(BaseModel):
    """POST /users operation=admin action=disable-user."""

    user_id: UUID
    reason: str | None = Field(default=None, max_length=256)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class AdminEnableUserIn(BaseModel):
    """POST /users operation=admin action=enable-user."""

    user_id: UUID
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class AdminForceLogoutIn(BaseModel):
    """POST /users operation=admin action=force-logout."""

    user_id: UUID
    reason: str | None = Field(default=None, max_length=256)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class AdminDeleteUserIn(BaseModel):
    """POST /users operation=admin action=delete-user (hard delete).

    `confirm` debe matchear exactamente `HARD-DELETE-USER-<user_id>`. Se
    valida con `model_validator(mode='after')` (NO field_validator: el
    orden de campos no esta garantizado en Pydantic v2, y mode='after'
    asegura que ambos campos ya pasaron su validacion individual).
    """

    user_id: UUID
    confirm: str = Field(..., min_length=20)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    @model_validator(mode='after')
    def _confirm_matches_user_id(self) -> AdminDeleteUserIn:
        if self.confirm != f'HARD-DELETE-USER-{self.user_id}':
            msg = 'confirm sentinel must match HARD-DELETE-USER-<user_id>'
            raise ValueError(msg)
        return self


class AdminListAdminActionsIn(BaseModel):
    """POST /users operation=admin action=list-admin-actions."""

    from_date: datetime | None = None
    to_date: datetime | None = None
    page_size: int = Field(default=50, ge=1, le=200)
    cursor: UUID | None = None
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')
