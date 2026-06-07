"""Modelos Pydantic de la operacion `geo`."""

from __future__ import annotations

from models._common import DateRange, RequestMeta
from shared.core.pydantic_types import ConfigDict, Field

_LIMIT_DEFAULT = 50
_LIMIT_MAX = 200


class ByCountryInput(DateRange):
    """GET ?operation=geo&action=by-country&from=&to=&limit="""

    limit: int = Field(default=_LIMIT_DEFAULT, ge=1, le=_LIMIT_MAX)
    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
