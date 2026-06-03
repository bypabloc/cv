"""Bloques Pydantic compartidos por los modelos de input del Lambda
`analytics`.

- `RequestMeta`: metadata de transporte que inyecta `http_handler` en
  `data._meta` (incluye `authorization`, que el `auth_guard` lee para
  validar el access JWT).
- `DateRange`: from/to opcionales con defaults (ultimos 30d) y max 90d.
- `Pagination`: page >= 1, page_size 1-200.

Prefijo `_` en el modulo: helpers compartidos, no es una action.
"""

from __future__ import annotations

from datetime import date, timedelta

from shared.core.pydantic_types import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

_DEFAULT_DAYS = 30
_MAX_DAYS = 90
_PAGE_SIZE_DEFAULT = 50
_PAGE_SIZE_MAX = 200


class RequestMeta(BaseModel):
    """Metadata de transporte inyectada por `http_handler` en `data._meta`.

    El `auth_guard` lee `authorization`; el `rate_limit_guard` lee `ip` y
    `country`. El resto se declara para no romper el `extra:forbid` del
    sub-modelo (http_handler inyecta TODOS estos campos para uniformidad).
    """

    ip: str = ''
    country: str | None = None
    user_agent: str | None = None
    bypass_token: str | None = None
    cloudfront_meta: dict[str, str] = Field(default_factory=dict)
    origin: str | None = None
    # Header Authorization (`Bearer <access JWT>`). Lo lee el auth_guard.
    authorization: str | None = None

    model_config = ConfigDict(extra='forbid')


class DateRange(BaseModel):
    """Rango de fechas comun: from/to opcionales, defaults 30d, max 90d.

    Convencion del rango: `date_to` representa el limite superior
    EXCLUSIVO del dia indicado (las queries usan `< date_to_exclusive`,
    que es `date_to + 1 dia`). `date_to_exclusive` lo exponen los services
    al bindear el SQL. Asi el dia `to` queda incluido en el resultado.
    """

    date_from: date | None = Field(default=None, alias='from')
    date_to: date | None = Field(default=None, alias='to')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    @model_validator(mode='after')
    def _fill_defaults_and_validate_span(self) -> DateRange:
        """Aplica defaults (ultimos 30d) y valida el span (max 90d)."""
        today = date.today()
        if self.date_to is None:
            self.date_to = today
        if self.date_from is None:
            self.date_from = self.date_to - timedelta(days=_DEFAULT_DAYS)
        if self.date_from > self.date_to:
            raise ValueError('from > to')
        span = (self.date_to - self.date_from).days
        if span > _MAX_DAYS:
            raise ValueError(
                'rango de fechas excede el maximo permitido (90 dias)'
            )
        return self

    def date_to_exclusive(self) -> date:
        """Limite superior EXCLUSIVO para el SQL (`< date_to_exclusive`).

        Es `date_to + 1 dia`, para que el dia `to` quede incluido (la
        convencion half-open de la seccion 0 de 04-queries-sql).
        """
        assert self.date_to is not None  # garantizado por el validator
        return self.date_to + timedelta(days=1)


class Pagination(BaseModel):
    """Paginacion comun: page >= 1, page_size 1-200 (default 50)."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=_PAGE_SIZE_DEFAULT, ge=1, le=_PAGE_SIZE_MAX)

    model_config = ConfigDict(extra='ignore')

    def offset(self) -> int:
        """OFFSET para el SQL (`LIMIT page_size OFFSET offset`)."""
        return (self.page - 1) * self.page_size
