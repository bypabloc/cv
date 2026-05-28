"""Modelos Pydantic de la operation `verify` (set password + resend code).

2 actions:
- `set-password`: el visitante define su password tras verify-magic-link
  o verify-code (paso opcional en flujo register).
- `resend-code`: re-emite un code/magic-link nuevo (en register o login).
"""

from __future__ import annotations

from shared.core import BaseModel, ConfigDict, Field

from ._common import _Meta


class VerifySetPasswordIn(BaseModel):
    """POST /auth operation=verify action=set-password.

    `password`: min 12 chars (politica MVP). Hashing con argon2id en
    el service.
    `temp_token`: rolling temp JWT del flujo activo (typ=temp,
    flow='register'|'login', step >=2 tras la verify del code/link).
    """

    password: str = Field(..., min_length=12, max_length=128)
    temp_token: str = Field(..., min_length=20)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class VerifyResendCodeIn(BaseModel):
    """POST /auth operation=verify action=resend-code.

    Re-emite code + magic-link nuevos. El service aplica rate-limit
    propio (max 1 resend cada 60s, max 3 en 5min — seed declarado en
    rate-limit-rules).
    """

    temp_token: str = Field(..., min_length=20)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
