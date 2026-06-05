"""Modelos Pydantic de la operation `login`.

3 actions, espejo de `register` (mismas shapes; el controller cambia el
flujo de validacion / persistencia).
"""

from __future__ import annotations

from shared.core.pydantic_types import BaseModel, ConfigDict, EmailStr, Field

from ._common import Niche, _Meta


class LoginStartIn(BaseModel):
    """POST /auth operation=login action=start.

    Plan login-mfa-list-redesign: el user se resuelve por el `sub` del temp
    precheck (Authorization), NO por el email del body. La password ya NO va
    en `start` (es un metodo mas de la lista, se verifica con
    `login.verify-password`).

    `email` es OPCIONAL y solo se usa en el UNICO caso de ALTA: un email
    nuevo cuyo precheck lleva un sub placeholder que no resuelve user — ahi
    el controller crea el pending con `email`. El email NUNCA viaja en el JWT
    (solo el sub=uuid). Si el sub resuelve un user, el email del body se
    ignora (anti-cross-account).
    """

    email: EmailStr | None = None
    cf_turnstile_response: str = Field(default='', max_length=2048)
    niche: Niche | None = None
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class LoginCheckEmailIn(BaseModel):
    """POST /auth operation=login action=check-email.

    Paso 1 del login unificado: dado un email (con Turnstile), reporta si
    existe y si tiene password configurado, SIN exponer la lista de metodos
    MFA (esa se revela tras verify-password). Bloque C.
    """

    email: EmailStr
    cf_turnstile_response: str = Field(default='', max_length=2048)
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
    """POST /auth operation=login action=verify-password.

    Plan login-mfa-list-redesign: `password` es UN metodo mas del checklist.
    Recibe el `temp_token` step=2 (`flow='login-mfa[:...]'` emitido por
    `login.start`) + `password`. El controller valida con argon2, suma
    `'password'` a los satisfechos y delega en `decide_mfa_step` (emite los
    factores faltantes o access+refresh si ya estan todos).
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
