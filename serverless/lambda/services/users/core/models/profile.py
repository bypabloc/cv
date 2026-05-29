"""Modelos Pydantic de la operation `profile` (plan 03).

5 actions: get, update (parcial), change-email (inicia magic-link),
confirm-email-change (publico, token del magic-link) y delete-account
(self-service GDPR con sentinel).

Todas requieren access JWT en `_meta.authorization` salvo
`confirm-email-change`, que se autentica por el token opaco del
magic-link (lo clickea el user en su email NUEVO, sin Bearer).
"""

from __future__ import annotations

from typing import Literal

from shared.core import BaseModel, ConfigDict, EmailStr, Field

from ._common import _Meta


class ProfileGetIn(BaseModel):
    """POST /users operation=profile action=get (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class ProfileUpdateIn(BaseModel):
    """POST /users operation=profile action=update (parcial).

    Cualquier subset de los campos editables. `None` = no cambiar.
    """

    display_name: str | None = Field(default=None, max_length=64)
    locale: Literal['es', 'en'] | None = None
    timezone: str | None = Field(default=None, max_length=64)
    marketing_consent: bool | None = None
    privacy_policy_version: str | None = Field(default=None, max_length=16)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class ProfileChangeEmailIn(BaseModel):
    """POST /users operation=profile action=change-email.

    Inicia el flow: valida que `new_email` este libre, (si el user tiene
    password) la valida, genera un magic-link al email NUEVO.
    """

    new_email: EmailStr
    password: str | None = Field(default=None, min_length=12, max_length=256)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class ProfileConfirmEmailChangeIn(BaseModel):
    """POST /users operation=profile action=confirm-email-change.

    Publico (sin Bearer): el user clickea el magic-link de su email NUEVO.
    `token` es el token opaco del magic-link (32 bytes b64url).
    """

    token: str = Field(..., min_length=20, max_length=256)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class ProfileDeleteAccountIn(BaseModel):
    """POST /users operation=profile action=delete-account.

    `confirm` debe ser exactamente el sentinel `DELETE-MY-ACCOUNT`.
    """

    confirm: Literal['DELETE-MY-ACCOUNT']
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')
