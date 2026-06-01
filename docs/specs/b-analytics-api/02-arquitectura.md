# 02 — Arquitectura

[< 01-contexto-y-decision](01-contexto-y-decision.md) | [Siguiente: 03-infraestructura >](03-infraestructura.md)

> Este plan es FULL-STACK: tiene 2 capas. (A) **Backend** — el Lambda
> `analytics` con auth JWT + queries + cache + rate-limit (secciones
> 1-10). (B) **Frontend** — la UI de metricas (features Next.js) que se
> monta DENTRO del app shell del admin (`admin-shell`, entregado por el
> plan `a-admin`) y consume el Lambda con `Authorization: Bearer <JWT>`
> (seccion 11). La UI vive bajo `/metrics` y rutas por feature, NUNCA
> bajo `/dashboard`.

## 1. Flujo end-to-end

```text
Browser/curl
  -> https://api.portfolio.{dev|stage|prod}.the-full-stack.com/analytics
       ?operation=<op>&action=<act>&from=YYYY-MM-DD&to=YYYY-MM-DD&...
  -> API Gateway REST (custom domain)
  -> Lambda `analytics` (SnapStart, arm64, py3.13, 512MB)
       handler.py
         -> shared.lambda_kit.http_handler(event, event_model, cors='echo', 200)
              -> extract_request(event) -> {operation, action, data, method}
              -> inject data._meta = {ip, country, user_agent, authorization, ...}
              -> run_controller({operation, action, data}, event_model)
                   -> import_controller -> OPERATIONS[op][act]
                   -> Controller(BaseController).execute()
                        -> auth_guard.require_active_user(_meta.authorization)
                             -> shared.auth.verify_jwt (HS256, jwt-secret SSM)
                             -> sin Bearer / JWT invalido -> 401 (code 4010)
                        -> rate_limit_guard.guard(ip, country)
                             -> shared.rate_limit.check_or_raise
                        -> service.<action>(...validated_data...)
                             -> @cached(ttl=60)  (solo agregadas)
                                  -> shared.db.db_session() -> Neon SQL
                                  -> rows -> dict serializable
                        -> {is_valid: true, data: {...}, code: 0}
              -> json_response(payload, status=200, cors='echo')
  -> admin (admin.portfolio.{env}.the-full-stack.com) / curl
```

## 2. Inventario de operations y actions

15 actions distribuidos en 8 operations:

| Operation | Action | Tipo | Cache | Endpoint shape |
|-----------|--------|------|-------|----------------|
| `analytics` | `overview` | agregada | si | KPIs top-level |
| `analytics` | `timeseries` | agregada | si | serie temporal |
| `analytics` | `top-pages` | ranking | si | top N pages |
| `analytics` | `top-referrers` | ranking | si | top referrers + UTM |
| `analytics` | `top-niches` | ranking | si | top niches |
| `analytics` | `active-now` | live | NO (ttl=10s) | sessions activas |
| `analytics` | `retention` | agregada | si | new vs returning |
| `events` | `distribution` | agregada | si | event_types share |
| `events` | `list` | listado | NO | eventos crudos paginados |
| `events` | `heatmap` | agregada | si | dia_semana x hora |
| `sessions` | `list` | listado | NO | sessions paginadas |
| `sessions` | `detail` | crudo | NO | 1 session + visits + count events |
| `visits` | `list` | listado | NO | visits paginadas |
| `visits` | `landing-pages` | ranking | si | top landing pages |
| `geo` | `by-country` | agregada | si | sessions por country |
| `devices` | `breakdown` | agregada | si | device/browser/os share |
| `funnel` | `conversion` | agregada | si | session->visit->contact |
| `contacts` | `list` | listado | NO | contacts paginados |
| `contacts` | `by-status` | agregada | si | distribucion por status |

**Total**: 8 operations, 19 actions, 12 con cache (TTL 60s), 1 con TTL
corto (10s, active-now), 6 sin cache (listados crudos y detail).

## 3. Layout del Lambda

```
serverless/lambda/services/analytics/
├── manifest.yaml
├── pyproject.toml
├── README.md                            # corto, link a docs/specs/
├── events/                              # eventos para `serverless run`
│   ├── overview.json
│   ├── timeseries.json
│   ├── top_pages.json
│   ├── top_referrers.json
│   ├── top_niches.json
│   ├── active_now.json
│   ├── retention.json
│   ├── events_distribution.json
│   ├── events_list.json
│   ├── events_heatmap.json
│   ├── sessions_list.json
│   ├── sessions_detail.json
│   ├── visits_list.json
│   ├── visits_landing_pages.json
│   ├── geo_by_country.json
│   ├── devices_breakdown.json
│   ├── funnel_conversion.json
│   ├── contacts_list.json
│   └── contacts_by_status.json
├── core/
│   ├── __init__.py
│   ├── handler.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── operations.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── _common.py                   # DateRange, Pagination, _Meta
│   │   ├── analytics.py
│   │   ├── events.py
│   │   ├── sessions.py
│   │   ├── visits.py
│   │   ├── geo.py
│   │   ├── devices.py
│   │   ├── funnel.py
│   │   └── contacts.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── analytics/
│   │   │   ├── __init__.py
│   │   │   ├── overview.py
│   │   │   ├── timeseries.py
│   │   │   ├── top_pages.py
│   │   │   ├── top_referrers.py
│   │   │   ├── top_niches.py
│   │   │   ├── active_now.py
│   │   │   └── retention.py
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── distribution.py
│   │   │   ├── list.py
│   │   │   └── heatmap.py
│   │   ├── sessions/
│   │   │   ├── __init__.py
│   │   │   ├── list.py
│   │   │   └── detail.py
│   │   ├── visits/
│   │   │   ├── __init__.py
│   │   │   ├── list.py
│   │   │   └── landing_pages.py
│   │   ├── geo/
│   │   │   ├── __init__.py
│   │   │   └── by_country.py
│   │   ├── devices/
│   │   │   ├── __init__.py
│   │   │   └── breakdown.py
│   │   ├── funnel/
│   │   │   ├── __init__.py
│   │   │   └── conversion.py
│   │   └── contacts/
│   │       ├── __init__.py
│   │       ├── list.py
│   │       └── by_status.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analytics_service.py
│   │   ├── events_service.py
│   │   ├── sessions_service.py
│   │   ├── visits_service.py
│   │   ├── geo_service.py
│   │   ├── devices_service.py
│   │   ├── funnel_service.py
│   │   └── contacts_service.py
│   └── utils/
│       ├── __init__.py
│       └── rate_limit_guard.py
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── _helpers.py
    │   ├── models/                      # 1 archivo por escenario por modelo
    │   ├── services/                    # mock SQLAlchemy session
    │   ├── controllers/                 # mock service
    │   └── handler/
    └── integration/
        ├── conftest.py                  # NO mocks: Neon test DB
        ├── _fixtures/
        └── test_*_e2e.py
```

## 4. EventModel + OPERATIONS

`core/settings/operations.py`:

```python
OPERATIONS: dict[str, dict[str, dict[str, str]]] = {
    'analytics': {
        'overview':       {'controller_module': 'controllers.analytics.overview',       'class': 'Overview'},
        'timeseries':     {'controller_module': 'controllers.analytics.timeseries',     'class': 'Timeseries'},
        'top-pages':      {'controller_module': 'controllers.analytics.top_pages',      'class': 'TopPages'},
        'top-referrers':  {'controller_module': 'controllers.analytics.top_referrers',  'class': 'TopReferrers'},
        'top-niches':     {'controller_module': 'controllers.analytics.top_niches',     'class': 'TopNiches'},
        'active-now':     {'controller_module': 'controllers.analytics.active_now',     'class': 'ActiveNow'},
        'retention':      {'controller_module': 'controllers.analytics.retention',      'class': 'Retention'},
    },
    'events': {
        'distribution':   {'controller_module': 'controllers.events.distribution', 'class': 'Distribution'},
        'list':           {'controller_module': 'controllers.events.list',         'class': 'List'},
        'heatmap':        {'controller_module': 'controllers.events.heatmap',      'class': 'Heatmap'},
    },
    'sessions': {
        'list':           {'controller_module': 'controllers.sessions.list',   'class': 'List'},
        'detail':         {'controller_module': 'controllers.sessions.detail', 'class': 'Detail'},
    },
    'visits': {
        'list':           {'controller_module': 'controllers.visits.list',           'class': 'List'},
        'landing-pages':  {'controller_module': 'controllers.visits.landing_pages',  'class': 'LandingPages'},
    },
    'geo': {
        'by-country':     {'controller_module': 'controllers.geo.by_country', 'class': 'ByCountry'},
    },
    'devices': {
        'breakdown':      {'controller_module': 'controllers.devices.breakdown', 'class': 'Breakdown'},
    },
    'funnel': {
        'conversion':     {'controller_module': 'controllers.funnel.conversion', 'class': 'Conversion'},
    },
    'contacts': {
        'list':           {'controller_module': 'controllers.contacts.list',      'class': 'List'},
        'by-status':      {'controller_module': 'controllers.contacts.by_status', 'class': 'ByStatus'},
    },
}
```

`core/handler.py`:

```python
from shared.http import http_handler
from shared.lambda_kit import build_event_model
from shared.observability import logger, metrics, tracer

from core.settings.operations import OPERATIONS

_EVENT_MODEL = build_event_model(OPERATIONS, allowed_methods=('GET',))


@logger.inject_lambda_context(log_event=False, correlation_id_path='requestContext.requestId')
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: object) -> dict:
    return http_handler(
        event,
        event_model=_EVENT_MODEL,
        cors_origin='echo',
        success_status=200,
        metric_names={
            'submitted': 'AnalyticsQuery',
            'rejected':  'AnalyticsRejected',
            'error':     'AnalyticsError',
        },
    )
```

> `cors_origin='echo'` (Decision 8): el CORS refleja el Origin del admin,
> NO `'public'`/`'*'`. El access JWT viaja en `Authorization: Bearer` y lo
> valida el `auth_guard` (seccion 7.1) ANTES del rate-limit.

## 5. Modelos Pydantic — diseno

### 5.1 Bloques compartidos (`core/models/_common.py`)

```python
from datetime import date, datetime
from shared.core import BaseModel, ConfigDict, Field, field_validator, model_validator


class _Meta(BaseModel):
    """Inyectado por http_handler desde headers + requestContext."""
    model_config = ConfigDict(populate_by_name=True)
    ip: str | None = Field(default=None, alias='ip')
    country: str | None = Field(default=None, alias='country')
    user_agent: str | None = Field(default=None, alias='user_agent')


class DateRange(BaseModel):
    """Validador comun: from/to opcionales, max 90 dias."""
    date_from: date | None = Field(default=None, alias='from')
    date_to:   date | None = Field(default=None, alias='to')
    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def _fill_defaults_and_validate_span(self) -> 'DateRange':
        today = date.today()
        if self.date_to is None:
            self.date_to = today
        if self.date_from is None:
            from datetime import timedelta
            self.date_from = self.date_to - timedelta(days=30)
        if self.date_from > self.date_to:
            raise ValueError('from > to')
        span = (self.date_to - self.date_from).days
        if span > 90:
            raise ValueError('rango de fechas excede el maximo permitido (90 dias)')
        return self


class Pagination(BaseModel):
    page:      int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
```

### 5.2 Un modelo Pydantic por (operation, action)

Patron:

```python
# core/models/analytics.py
from shared.core import BaseModel, ConfigDict, Field
from ._common import DateRange, _Meta


class OverviewInput(DateRange):
    """GET ?operation=analytics&action=overview&from=&to="""
    meta: _Meta | None = Field(default=None, alias='_meta')
    model_config = ConfigDict(populate_by_name=True)


class TimeseriesInput(DateRange):
    """?bucket=day|hour, ?niche=optional, ?event_type=optional"""
    bucket:     str | None  = Field(default='day', pattern=r'^(day|hour|week)$')
    niche:      str | None  = Field(default=None, max_length=32)
    event_type: str | None  = Field(default=None, max_length=64)
    meta:       _Meta | None = Field(default=None, alias='_meta')
    model_config = ConfigDict(populate_by_name=True)


class TopPagesInput(DateRange):
    limit: int = Field(default=10, ge=1, le=50)
    niche: str | None = Field(default=None, max_length=32)
    meta:  _Meta | None = Field(default=None, alias='_meta')
    model_config = ConfigDict(populate_by_name=True)


# ... idem TopReferrersInput, TopNichesInput, ActiveNowInput, RetentionInput
```

Repeticion del patron en `events.py`, `sessions.py`, etc. Validar el
shape MINIMO necesario por endpoint — no validar campos opcionales que
se pasen al SQL sin filtrar.

## 6. Controllers — patron uniforme

Todos los controllers heredan de `BaseController` (de `shared.lambda_kit`)
y tienen este shape:

```python
# core/controllers/analytics/overview.py
from typing import Any

from shared.lambda_kit import BaseController
from shared.observability import logger

from core.models.analytics import OverviewInput
from core.services.analytics_service import overview as _overview
from core.utils.rate_limit_guard import guard


class Overview(BaseController):
    event_model = OverviewInput

    def execute(self) -> dict[str, Any]:
        data: OverviewInput = self.validated_data
        guard(meta=data.meta, endpoint='/analytics')
        result = _overview(date_from=data.date_from, date_to=data.date_to)
        return {
            'is_valid': True,
            'code': 0,
            'data': result,
        }
```

Reglas:

- 1 archivo = 1 controller = 1 action.
- Nombre de clase = `action.capitalize().replace('-', '_')` (`top-pages`
  -> `TopPages`).
- `event_model` apunta al input Pydantic correspondiente.
- `execute()` SIEMPRE: (1) rate-limit guard, (2) service call,
  (3) return shape.
- NO mete logica de negocio. Si una operacion necesita mas de 1 service
  call, el orchestrador vive en el service (no en el controller).

## 7. Services — patron uniforme

Los services concentran:

- Query SQL (via `shared.db.db_session` + select/func/Session).
- Agregaciones / normalizaciones.
- Decorador `@cached` cuando aplica.
- Errores normalizados (excepciones a `ServiceError` que el controller
  mapea a `{is_valid:false, code:5xxx}`).

```python
# core/services/analytics_service.py
from datetime import date
from typing import Any, Final

from shared.cache import cached
from shared.db import db_session, func, select
from shared.observability import logger
from shared.db.models.visitor import Contact, Session, SessionVisit, TrackingEvent


_CACHE_TAGS: Final[list[str]] = ['analytics-aggregate']


@cached(ttl=60, namespace='analytics:overview', tags=_CACHE_TAGS)
def overview(*, date_from: date, date_to: date) -> dict[str, Any]:
    with db_session() as s:
        # 5 queries en paralelo logico (cada una es 1 round-trip a Neon)
        sessions_count = s.scalar(
            select(func.count())
            .select_from(Session)
            .where(Session.first_seen_at >= date_from, Session.first_seen_at < date_to)
        )
        visits_count = s.scalar(
            select(func.count())
            .select_from(SessionVisit)
            .where(SessionVisit.started_at >= date_from, SessionVisit.started_at < date_to)
        )
        events_count = s.scalar(
            select(func.count())
            .select_from(TrackingEvent)
            .where(TrackingEvent.created_at >= date_from, TrackingEvent.created_at < date_to)
        )
        contacts_count = s.scalar(
            select(func.count())
            .select_from(Contact)
            .where(Contact.created_at >= date_from, Contact.created_at < date_to)
        )
        unique_visitors = s.scalar(
            select(func.count(func.distinct(SessionVisit.session_id)))
            .where(SessionVisit.started_at >= date_from, SessionVisit.started_at < date_to)
        )
        avg_visit_duration = s.scalar(
            select(func.coalesce(func.avg(
                func.extract('epoch', SessionVisit.ended_at - SessionVisit.started_at)
            ), 0))
            .where(SessionVisit.ended_at.is_not(None),
                   SessionVisit.started_at >= date_from,
                   SessionVisit.started_at < date_to)
        )
        # bounce rate: visits con event_count == 1 / total visits
        bounce_visits = s.scalar(
            select(func.count())
            .select_from(SessionVisit)
            .where(SessionVisit.event_count == 1,
                   SessionVisit.started_at >= date_from,
                   SessionVisit.started_at < date_to)
        )
    bounce_rate = (bounce_visits / visits_count) if visits_count else 0.0
    return {
        'sessions': int(sessions_count or 0),
        'visits':   int(visits_count or 0),
        'events':   int(events_count or 0),
        'contacts': int(contacts_count or 0),
        'unique_visitors': int(unique_visitors or 0),
        'avg_visit_duration_sec': float(avg_visit_duration or 0),
        'bounce_rate': float(bounce_rate),
        'from': date_from.isoformat(),
        'to':   date_to.isoformat(),
    }
```

> El SQL detallado de cada service esta en
> [04-queries-sql.md](04-queries-sql.md).

## 8. Rate-limit guard

`core/utils/rate_limit_guard.py`:

```python
from typing import Final

from shared.rate_limit import check_or_raise
from shared.observability import logger

from core.models._common import _Meta


_ENDPOINT: Final[str] = '/analytics'


def guard(*, meta: _Meta | None, endpoint: str = _ENDPOINT) -> None:
    """Llama a check_or_raise con la metadata extraida del request.

    Levanta RateLimitExceededError / IPBlacklistedError / CountryBlockedError
    que `http_handler` mapea a 429/403 con codes 4290/4030/4031.
    """
    ip = (meta.ip if meta else None) or 'unknown'
    country = meta.country if meta else None
    check_or_raise(
        ip=ip,
        endpoint=endpoint,
        country=country,
        turnstile_validated=False,  # GET no usa Turnstile
    )
```

La regla `/analytics` se inserta en la tabla `rate-limit-rules` al
provisionar el Lambda — ver [03-infraestructura.md](03-infraestructura.md).

## 9. Error handling

`core/settings/config.py` define enums:

```python
from enum import IntEnum, StrEnum


class ErrorCode(IntEnum):
    OK                 = 0
    VALIDATION         = 1000
    DATE_RANGE         = 1001
    PAGE_SIZE          = 1002
    INVALID_PARAM      = 1003
    NOT_FOUND          = 4040
    BLACKLISTED        = 4030
    COUNTRY_BLOCKED    = 4031
    RATE_LIMITED       = 4290
    EXTERNAL           = 5100
    INTERNAL           = 6000


class LogMetricType(StrEnum):
    QUERY_OK       = 'AnalyticsQueryOk'
    QUERY_REJECTED = 'AnalyticsQueryRejected'
    QUERY_ERROR    = 'AnalyticsQueryError'
    CACHE_HIT      = 'AnalyticsCacheHit'
    CACHE_MISS     = 'AnalyticsCacheMiss'
```

Mapeo errores -> HTTP status (lo hace `http_handler` desde el code):

| code | status | excepcion / contexto |
|------|--------|----------------------|
| 0 | 200 | OK |
| 1000-1099 | 400 | Pydantic ValidationError / param invalido |
| 4030 | 403 | IPBlacklistedError |
| 4031 | 403 | CountryBlockedError |
| 4040 | 404 | sessions/detail con session_id inexistente |
| 4290 | 429 | RateLimitExceededError |
| 5100 | 503 | error transitorio DB (timeout, connection) |
| 6000 | 500 | error interno no clasificado |

## 10. Cold start path

- Modulo-scope: `import shared.lambda_kit`, `import shared.http`,
  `OPERATIONS`, `build_event_model(OPERATIONS)` se ejecutan una sola
  vez por container.
- `db_session` -> `get_engine()` se inicializa LAZY en la primera query
  (no en cold start) para que el Restore de SnapStart no necesite una
  conexion Neon activa. La conexion se establece en el primer handler
  invoke.
- SnapStart hook (`runtime_hooks.py`): NO precalentar la conexion a DB
  — Neon scale-to-zero la cerraria; en cambio precalentar
  `OPERATIONS`, `build_event_model`, importar todos los controllers.

## 11. Capa de frontend — UI de metricas (Next.js)

La UI de metricas consume el Lambda `analytics` y se monta DENTRO del
app shell del admin. El shell (header + sidebar + nav + layout protegido
`(admin)/layout.tsx` con AuthGuard) lo entrega el plan `a-admin` (feature
`admin-shell`); este plan AGREGA las features de metricas a esa misma app
(`admin/`, package `@portfolio/admin`).

> La feature `sessions` de ESTE plan es el tracking de VISITANTES (lista
> de sesiones de visitas, su detalle, geo, device). NO confundir con la
> feature `sessions-mgmt` del plan `a-admin` (las sesiones de MI cuenta
> auth: revocar mi login en otro dispositivo). Son cosas distintas.

### 11.1 Stack (heredado de `a-admin`)

| Capa | Eleccion |
|------|----------|
| Framework | Next.js 16.2.6 `output: 'export'` (SPA estatica) |
| UI | React 19.2.6 (ref-as-prop, sin `forwardRef`) + TypeScript 6 strict |
| Estilos | Tailwind v4 + shadcn/ui (tokens del DS, dark/light via next-themes) |
| Charts | Recharts (via `shadcn add chart`, color por CSS vars) |
| Tablas | shadcn `Table` + Tanstack Table v8 + Tanstack Virtual (listas grandes) |
| Data fetching | Tanstack Query v5 (`useQuery`/`useSuspenseQuery`) |
| State auth | Zustand (`useAuthStore`) del plan `a-admin` (NO se duplica) |
| Mocks (dev/test) | MSW v2 (`tests/mocks/handlers.ts`) hasta que el Lambda este vivo |

No se introduce ninguna lib nueva: todo ya esta declarado por `a-admin`.
Ver la skill `admin-stack` y `.claude/rules/admin.md` para el detalle.

### 11.2 Features y rutas

Una feature Next.js por dominio del backend, bajo `admin/src/features/`.
Las pages viven en el route group `(admin)/` (protegido por el AuthGuard
del shell). Rutas bajo `/metrics` + por feature, NUNCA `/dashboard`:

| Feature | Ruta(s) | Backend (operation/action) |
|---------|---------|----------------------------|
| `analytics` | `/metrics` (overview), `/metrics/timeseries` | `analytics`: overview, timeseries, top-pages, top-referrers, top-niches, active-now, retention |
| `sessions` (tracking) | `/sessions`, `/sessions/[id]` | `sessions`: list, detail |
| `events` | `/events` | `events`: distribution, list, heatmap |
| `visits` | `/visits` | `visits`: list, landing-pages |
| `geo` | `/geo` | `geo`: by-country |
| `devices` | `/devices` | `devices`: breakdown |
| `funnel` | `/funnel` | `funnel`: conversion |
| `contacts` | `/contacts` | `contacts`: list, by-status |

`/metrics` es la raiz del area de metricas (overview con KPIs +
active-now). El sidebar del shell ya tiene los slots/links a estas
secciones (declarados por `a-admin`); este plan los conecta a sus pages.

Cada feature sigue el layout Hybrid Atomic Design de `admin/`:

```text
admin/src/features/<dominio>/
├── api/
│   ├── <dominio>-client.ts      # fns que llaman el api-client con Bearer
│   └── query-keys.ts            # queryKey factory del dominio
├── hooks/
│   └── use-<accion>.ts          # useQuery/useSuspenseQuery + staleTime
├── components/
│   ├── <Dominio>Overview.tsx    # KPIs / chart Recharts
│   ├── <Dominio>Table.tsx       # DataTable (Tanstack Table) + Virtual
│   └── ...
└── types.ts                     # shape de la respuesta del endpoint
```

### 11.3 Hooks Tanstack Query con auth Bearer

Todo fetch pasa por el `api-client` del admin (`admin/src/lib/api-client.ts`,
entregado por `a-admin`): adjunta `Authorization: Bearer <access JWT>`
del `useAuthStore`, maneja el refresh rotation con mutex y reintenta el
request tras un 401. NUNCA se llama `fetch()` directo desde un componente
ni desde un hook.

```ts
// admin/src/features/analytics/hooks/use-overview.ts
import { useSuspenseQuery } from '@tanstack/react-query'

import { analyticsKeys } from '../api/query-keys'
import { fetchOverview } from '../api/analytics-client'
import type { OverviewRange } from '../types'

export function useOverview(range: OverviewRange) {
  return useSuspenseQuery({
    queryKey: analyticsKeys.overview(range),
    queryFn: () => fetchOverview(range),
    staleTime: 60_000,
  })
}
```

```ts
// admin/src/features/analytics/api/analytics-client.ts
import { apiClient } from '@/lib/api-client'

import type { OverviewRange, OverviewResponse } from '../types'

export async function fetchOverview(
  range: OverviewRange,
): Promise<OverviewResponse> {
  // apiClient inyecta Authorization: Bearer <JWT> + maneja refresh/retry
  return apiClient.get<OverviewResponse>('/analytics', {
    params: {
      operation: 'analytics',
      action: 'overview',
      from: range.from,
      to: range.to,
    },
  })
}
```

### 11.4 staleTime por endpoint

El `staleTime` de cada `useQuery` matchea el TTL de cache del backend
(seccion 2). Asi el cliente no refetchea data que el Lambda devuelve
cacheada:

| Feature / accion | staleTime | refetchInterval | Notas |
|------------------|-----------|-----------------|-------|
| `analytics` agregadas (overview, timeseries, top-*, retention) | `60_000` | — | matchea TTL backend 60s |
| `analytics` active-now | `10_000` | `15_000` | live; TTL backend 10s |
| `events` distribution, heatmap | `60_000` | — | agregadas (cache backend) |
| `events` list | `30_000` | — | listado crudo (sin cache backend) |
| `sessions` list, detail | `30_000` (list) / `0` (detail) | — | detail siempre fresh |
| `visits` landing-pages | `60_000` | — | ranking (cache backend) |
| `visits` list | `30_000` | — | listado crudo |
| `geo` by-country, `devices` breakdown | `60_000` | — | agregadas |
| `funnel` conversion | `60_000` | — | agregada |
| `contacts` by-status | `60_000` | — | agregada |
| `contacts` list | `30_000` | — | listado crudo (PII) |

Regla transversal: `refetchOnWindowFocus: false` (SPA, sin refetch
automatico de fondo) salvo en `active-now`. Los listados con PII
(`contacts/list`, `sessions/*`) NO se persisten en el query persister
(filtrarlos con `defaultShouldDehydrateQuery`).

### 11.5 Dependencia del shell (`a-admin`)

La UI de metricas NO se puede empezar hasta que `a-admin` haya entregado:
el scaffold de `admin/`, el `admin-shell` (layout `(admin)/` + sidebar con
slots), el `useAuthStore` + `api-client` con Bearer/refresh, y el deploy a
Cloudflare Pages. Hasta que el Lambda `analytics` este vivo en el env, los
hooks corren contra MSW. Ver la matriz de dependencias en
[08-descomposicion-paralelizacion.md](08-descomposicion-paralelizacion.md).

[< 01-contexto-y-decision](01-contexto-y-decision.md) | [Siguiente: 03-infraestructura >](03-infraestructura.md)
