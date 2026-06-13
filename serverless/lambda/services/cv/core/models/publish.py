"""Modelos Pydantic de la operation `publish`.

2 actions sin payload de negocio: `dispatch` (dispara el workflow
deploy-apps.yml via la GitHub API) y `status` (consulta el ultimo run del
ref del stage). El `ref` lo resuelve el service desde el stage del Lambda
— el cliente NO lo elige (un admin de dev no puede deployar prod).
"""

from __future__ import annotations

from shared.core.pydantic_types import BaseModel, ConfigDict, Field

from ._common import _Meta


class PublishDispatchIn(BaseModel):
    """POST /cv operation=publish action=dispatch (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class PublishStatusIn(BaseModel):
    """POST /cv operation=publish action=status (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
