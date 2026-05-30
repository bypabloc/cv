"""Modelos Pydantic de la operation `register`.

3 actions:
- `start`: el visitante inicia el registro con su email + Turnstile.
- `verify-magic-link`: el visitante clickea el link del email
  (sin step intermedio).
- `verify-code`: el visitante pega el code de 8 chars en el dashboard.
"""

from __future__ import annotations

from shared.core.pydantic_types import BaseModel, ConfigDict, EmailStr, Field

from ._common import Niche, _Meta


class RegisterStartIn(BaseModel):
    """POST /auth operation=register action=start."""

    email: EmailStr
    # default='' (no min_length): un cf_turnstile_response vacio es el
    # gatillo del bypass de Turnstile para tests E2E (solo dev/local, ver
    # shared.crypto.captcha.verify_captcha_or_bypass). En prod, vacio + sin
    # bypass token valido -> el controller lanza TurnstileError 403 (AC-12).
    # La exigencia del token NO es a nivel Pydantic sino del controller.
    cf_turnstile_response: str = Field(default='', max_length=2048)
    niche: Niche | None = None
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class RegisterVerifyMagicLinkIn(BaseModel):
    """GET callback del magic-link (o POST si el dashboard re-hace la verify).

    `token` es el opaque 32-byte b64url que viajo en la URL del email.
    El controller resuelve el `user_id` por SHA-256(token) contra
    `auth_magic_links.token_hash`.
    """

    token: str = Field(..., min_length=32, max_length=128)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class RegisterVerifyCodeIn(BaseModel):
    """POST /auth operation=register action=verify-code.

    `code`: 8 chars Crockford-like (alphabet `[A-HJ-NP-Z2-9]` —
    excluye `O/0/I/1/L` para reducir confusion visual).
    `temp_token`: rolling temp JWT emitido en `register.start`.
    """

    code: str = Field(
        ...,
        min_length=8,
        max_length=8,
        pattern=r'^[A-HJ-NP-Z2-9]{8}$',
    )
    temp_token: str = Field(..., min_length=20)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
