"""Modelos Pydantic de la operation `security` (overview unificado).

1 action: overview. Requiere un access JWT valido en
`_meta.authorization` (lo valida `require_active_user` en el controller).
Sin payload propio (mismo patron que `MfaListIn`).
"""

from __future__ import annotations

from shared.core.pydantic_types import BaseModel, ConfigDict, Field

from ._common import _Meta


class SecurityOverviewIn(BaseModel):
    """GET /auth operation=security action=overview (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class SecurityPasswordSetRequiredIn(BaseModel):
    """POST /auth operation=security action=password-set-required.

    Marca/desmarca la password como factor `required` al loguear. Requiere
    access JWT. Sujeto al guard "siempre >=1 required" (no puede quedar el
    user sin ningun factor exigido).
    """

    required: bool = Field(...)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')
