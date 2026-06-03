"""Modelos Pydantic de la operacion `analytics` (8 actions).

- overview / retention: solo rango (heredan DateRange).
- timeseries: rango + bucket (day|hour|week) + niche/event_type opcionales.
- top-pages / top-niches: rango + limit (+ niche en top-pages).
- top-referrers: rango + limit.
- active-now: SIN rango (solo _meta) — modelo aparte que NO hereda DateRange.
- dashboard: union de los params de las 7 actions del overview de /metrics
  (rango + bucket + limit). Una sola request que agrega las 7 vistas.
"""

from __future__ import annotations

from models._common import DateRange, RequestMeta
from shared.core.pydantic_types import BaseModel, ConfigDict, Field

_LIMIT_DEFAULT = 10
_LIMIT_MAX = 50


class OverviewInput(DateRange):
    """GET ?operation=analytics&action=overview&from=&to="""

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class TimeseriesInput(DateRange):
    """GET ?operation=analytics&action=timeseries&bucket=&niche=&event_type="""

    bucket: str = Field(default='day', pattern='^(day|hour|week)$')
    niche: str | None = None
    event_type: str | None = None
    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class TopPagesInput(DateRange):
    """GET ?operation=analytics&action=top-pages&limit=&niche="""

    limit: int = Field(default=_LIMIT_DEFAULT, ge=1, le=_LIMIT_MAX)
    niche: str | None = None
    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class TopReferrersInput(DateRange):
    """GET ?operation=analytics&action=top-referrers&limit="""

    limit: int = Field(default=_LIMIT_DEFAULT, ge=1, le=_LIMIT_MAX)
    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class TopNichesInput(DateRange):
    """GET ?operation=analytics&action=top-niches&limit="""

    limit: int = Field(default=_LIMIT_DEFAULT, ge=1, le=_LIMIT_MAX)
    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class ActiveNowInput(BaseModel):
    """GET ?operation=analytics&action=active-now (SIN rango de fechas)."""

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class RetentionInput(DateRange):
    """GET ?operation=analytics&action=retention&from=&to="""

    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class DashboardInput(DateRange):
    """GET ?operation=analytics&action=dashboard&from=&to=&bucket=&limit=

    Union de los params de las 7 vistas del overview de /metrics:
    rango (from/to), bucket de la serie temporal (day|hour|week) y limit
    de los rankings (top-pages/referrers/niches). Una sola request que
    devuelve las 7 vistas agregadas + el contador live (active-now).
    """

    bucket: str = Field(default='day', pattern='^(day|hour|week)$')
    limit: int = Field(default=_LIMIT_DEFAULT, ge=1, le=_LIMIT_MAX)
    meta: RequestMeta = Field(default_factory=RequestMeta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
