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

from datetime import UTC, date, datetime, timedelta

from shared.core.pydantic_types import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

_DEFAULT_DAYS = 30
_MAX_DAYS = 90
_PAGE_SIZE_DEFAULT = 50
_PAGE_SIZE_MAX = 200


def _coerce_dt(value: object) -> datetime | None:
    """Coacciona un input from/to a datetime aware UTC (o None).

    Acepta tanto `date`/fecha-string `YYYY-MM-DD` (medianoche UTC) como
    `datetime`/ISO-string con hora. Un naive datetime se asume UTC.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime(value.year, value.month, value.day)
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    else:  # pragma: no cover - pydantic ya valida el tipo
        raise TypeError('from/to debe ser date o datetime')
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _input_has_time(value: object) -> bool:
    """True si el input traia hora explicita (datetime o ISO con `T`)."""
    if isinstance(value, datetime):
        return True
    if isinstance(value, str):
        return 'T' in value or ' ' in value.strip()
    return False  # date puro / None -> sin hora


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
    """Rango comun: from/to opcionales, defaults 30d, max 90d.

    Acepta tanto fechas (`YYYY-MM-DD`, medianoche UTC) como datetimes con
    hora (`YYYY-MM-DDTHH:MM:SSZ`). Internamente se normalizan a datetime
    aware UTC. Convencion del limite superior:

    - si `to` vino SIN hora (fecha pura): el dia `to` queda incluido ->
      `date_to_exclusive = to + 1 dia` (half-open clasico).
    - si `to` vino CON hora: el limite es EXCLUSIVO directo (la hora ya es
      precisa) -> `date_to_exclusive = to`.

    El span se valida por timedelta (max 90 dias) cubriendo ambos casos.
    """

    date_from: datetime | None = Field(default=None, alias='from')
    date_to: datetime | None = Field(default=None, alias='to')
    # Flag derivado del input crudo: el `to` traia hora explicita. Se
    # excluye del dump (no es parte del contrato publico).
    to_has_time: bool = Field(default=False, exclude=True)

    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    @field_validator('date_from', 'date_to', mode='before')
    @classmethod
    def _normalize_dt(cls, value: object) -> datetime | None:
        """Coacciona el input a datetime aware UTC (date o datetime)."""
        return _coerce_dt(value)

    @model_validator(mode='before')
    @classmethod
    def _track_to_has_time(cls, data: object) -> object:
        """Recuerda si el `to` original traia hora (para el limite)."""
        if isinstance(data, dict):
            raw_to = data.get('to', data.get('date_to'))
            data = dict(data)
            data['to_has_time'] = _input_has_time(raw_to)
        return data

    @model_validator(mode='after')
    def _fill_defaults_and_validate_span(self) -> DateRange:
        """Aplica defaults (ultimos 30d) y valida el span (max 90d)."""
        now = datetime.now(tz=UTC)
        if self.date_to is None:
            # Default `to`: medianoche de hoy (convencion half-open) -> el
            # dia actual queda incluido via date_to_exclusive (+1 dia).
            self.date_to = now.replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            self.to_has_time = False
        if self.date_from is None:
            self.date_from = self.date_to - timedelta(days=_DEFAULT_DAYS)
        if self.date_from > self.date_to:
            raise ValueError('from > to')
        if (self.date_to - self.date_from) > timedelta(days=_MAX_DAYS):
            raise ValueError(
                'rango de fechas excede el maximo permitido (90 dias)'
            )
        return self

    def date_to_exclusive(self) -> datetime:
        """Limite superior EXCLUSIVO para el SQL (`< date_to_exclusive`).

        `to + 1 dia` si vino como fecha pura (el dia `to` queda incluido);
        `to` tal cual si vino con hora (limite preciso).
        """
        assert self.date_to is not None  # garantizado por el validator
        if self.to_has_time:
            return self.date_to
        return self.date_to + timedelta(days=1)


class Pagination(BaseModel):
    """Paginacion comun: page >= 1, page_size 1-200 (default 50)."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=_PAGE_SIZE_DEFAULT, ge=1, le=_PAGE_SIZE_MAX)

    model_config = ConfigDict(extra='ignore')

    def offset(self) -> int:
        """OFFSET para el SQL (`LIMIT page_size OFFSET offset`)."""
        return (self.page - 1) * self.page_size
