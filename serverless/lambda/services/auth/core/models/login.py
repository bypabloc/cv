"""Modelos Pydantic de la operation `login`.

3 actions, espejo de `register` (mismas shapes; el controller cambia el
flujo de validacion / persistencia).
"""

from __future__ import annotations

from shared.core import BaseModel, ConfigDict, EmailStr, Field

from ._common import Niche, _Meta


class LoginStartIn(BaseModel):
    """POST /auth operation=login action=start."""

    email: EmailStr
    cf_turnstile_response: str = Field(..., min_length=1, max_length=2048)
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
