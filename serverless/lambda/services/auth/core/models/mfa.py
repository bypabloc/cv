"""Modelos Pydantic de la operation `mfa` (plan 02).

8 actions: setup-totp, confirm-totp, setup-email-code, set-preferred,
disable, list, recovery-codes-generate, recovery-codes-consume.

Todas requieren un access JWT valido en `_meta.authorization` (lo valida
`require_active_user` en el controller), salvo `recovery-codes-consume`
que usa un `temp_token` step=2 con `prev=password|webauthn` (decision 10).
"""

from __future__ import annotations

from typing import Literal

from shared.core import BaseModel, ConfigDict, Field

from ._common import _Meta


class MfaSetupTotpIn(BaseModel):
    """POST /auth operation=mfa action=setup-totp (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class MfaConfirmTotpIn(BaseModel):
    """POST /auth operation=mfa action=confirm-totp."""

    code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class MfaSetupEmailCodeIn(BaseModel):
    """POST /auth operation=mfa action=setup-email-code (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class MfaSetPreferredIn(BaseModel):
    """POST /auth operation=mfa action=set-preferred."""

    kind: Literal['totp', 'email_code']
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class MfaDisableIn(BaseModel):
    """POST /auth operation=mfa action=disable."""

    kind: Literal['totp', 'email_code']
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class MfaListIn(BaseModel):
    """GET /auth operation=mfa action=list (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class MfaRecoveryCodesGenerateIn(BaseModel):
    """POST /auth operation=mfa action=recovery-codes-generate (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class MfaRecoveryCodesConsumeIn(BaseModel):
    """POST /auth operation=mfa action=recovery-codes-consume.

    `temp_token` = JWT step=2 con `prev=password|webauthn` (decision 10).
    `code` = recovery code de 10 chars Crockford-like (sin O/0/I/1/L).
    """

    temp_token: str = Field(..., min_length=20)
    code: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r'^[A-HJ-NP-Z2-9]{10}$',
    )
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')
