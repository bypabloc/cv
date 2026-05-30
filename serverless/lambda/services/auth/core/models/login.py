"""Modelos Pydantic de la operation `login`.

3 actions, espejo de `register` (mismas shapes; el controller cambia el
flujo de validacion / persistencia).
"""

from __future__ import annotations

from shared.core.pydantic_types import BaseModel, ConfigDict, EmailStr, Field

from ._common import Niche, _Meta


class LoginStartIn(BaseModel):
    """POST /auth operation=login action=start.

    `password` es OPCIONAL (plan 02, decision 9): si viene, el controller
    lo valida con argon2 ANTES de devolver los methods (login con
    password directo). Si falta, comportamiento passwordless del plan 01
    (magic-link + code).
    """

    email: EmailStr
    # default='' (no min_length): habilita el bypass de Turnstile para
    # tests E2E (cf_response vacio + token Ed25519 firmado, solo dev/local).
    # En prod, vacio + sin bypass valido -> TurnstileError 403 en el
    # controller (AC-12). Igual que register.start y contact_form.
    cf_turnstile_response: str = Field(default='', max_length=2048)
    password: str | None = Field(default=None, max_length=256)
    niche: Niche | None = None
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class LoginVerifyMagicLinkIn(BaseModel):
    """GET callback del magic-link de login (mismo shape que register)."""

    token: str = Field(..., min_length=32, max_length=128)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class LoginVerifyCodeIn(BaseModel):
    """POST /auth operation=login action=verify-code (mismo shape)."""

    code: str = Field(
        ...,
        min_length=8,
        max_length=8,
        pattern=r'^[A-HJ-NP-Z2-9]{8}$',
    )
    temp_token: str = Field(..., min_length=20)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class LoginVerifyPasswordIn(BaseModel):
    """POST /auth operation=login action=verify-password (plan 02).

    Variante 2-step del login con password: `temp_token` step=1 (de un
    login.start sin password) + `password`. El controller valida con
    argon2 y, si match, emite access+refresh (sin MFA) o temp step=2 +
    methods (con MFA).
    """

    temp_token: str = Field(..., min_length=20)
    password: str = Field(..., min_length=12, max_length=256)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class LoginVerifyTotpIn(BaseModel):
    """POST /auth operation=login action=verify-totp (plan 02).

    Paso final del login con MFA TOTP: `temp_token` step=2
    (`prev=password|webauthn`) + `code` de 6 digitos.
    """

    temp_token: str = Field(..., min_length=20)
    code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
