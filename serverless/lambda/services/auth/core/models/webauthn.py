"""Modelos Pydantic de la operation `webauthn` (plan 02).

6 actions: register-options, register-verify, login-options,
login-verify, list-credentials, delete-credential.

`response` es el `PublicKeyCredential` JSON crudo del browser
(navigator.credentials.create/get .toJSON()); se valida solo como dict
aqui — la verificacion criptografica la hace `shared.auth.webauthn`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.core import BaseModel, ConfigDict, EmailStr, Field

from ._common import _Meta


class WebauthnRegisterOptionsIn(BaseModel):
    """POST /auth operation=webauthn action=register-options (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class WebauthnRegisterVerifyIn(BaseModel):
    """POST /auth operation=webauthn action=register-verify."""

    challenge_id: UUID
    response: dict[str, Any]
    nickname: str | None = Field(default=None, max_length=64)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class WebauthnLoginOptionsIn(BaseModel):
    """POST /auth operation=webauthn action=login-options."""

    email: EmailStr
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class WebauthnLoginVerifyIn(BaseModel):
    """POST /auth operation=webauthn action=login-verify."""

    challenge_id: UUID
    response: dict[str, Any]
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class WebauthnListCredentialsIn(BaseModel):
    """GET /auth operation=webauthn action=list-credentials (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class WebauthnDeleteCredentialIn(BaseModel):
    """POST /auth operation=webauthn action=delete-credential.

    `credential_id` es el `id` (UUID PK) del row, NO el credential_id
    BYTEA del authenticator.
    """

    credential_id: UUID
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')
