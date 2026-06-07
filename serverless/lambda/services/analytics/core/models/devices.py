"""Modelos Pydantic de la operacion `devices`."""

from __future__ import annotations

from models._common import DateRange, RequestMeta
from shared.core.pydantic_types import ConfigDict, Field


class BreakdownInput(DateRange):
    """GET ?operation=devices&action=breakdown&from=&to="""

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')
    model_config = ConfigDict(populate_by_name=True, extra='ignore')
