# 06 — Testing

[< 05-cache-layer](05-cache-layer.md) | [Siguiente: 07-archivos-afectados >](07-archivos-afectados.md)

## 1. Niveles

| Nivel | Ubicacion | Que se prueba | Aisla |
|-------|-----------|---------------|-------|
| Unit modelo | `tests/unit/models/test_<input>_<escenario>.py` | Pydantic models (defaults, validators, errores) | Sin Neon, sin DynamoDB |
| Unit service | `tests/unit/services/test_<service>_<action>_<escenario>.py` | Logica + queries SQL | Mock `db_session` con `MagicMock(scalar=...)` |
| Unit controller | `tests/unit/controllers/test_<action>_<escenario>.py` | Orquestacion: guard + service + shape | Mock del service + mock de `check_or_raise` |
| Unit handler | `tests/unit/handler/test_handler_<escenario>.py` | Routing: event -> operation -> controller | Mock del controller |
| Integration | `tests/integration/test_<flow>_e2e.py` | Flujo completo: HTTP event -> Lambda -> Neon | Neon test branch, DynamoDB test tables |

## 2. Regla de oro

> Un archivo = un escenario = una funcion `test_*`. El nombre del archivo
> ES el caso. El docstring del modulo describe Given/When/Then. El cuerpo
> es Arrange-Act-Assert.

Ejemplo:

```python
# tests/unit/models/test_overview_input_when_no_dates_then_defaults_last_30d.py
"""
Given una request sin from/to,
When se valida OverviewInput,
Then date_to=hoy y date_from=hoy-30d.
"""
from datetime import date, timedelta

from core.models.analytics import OverviewInput


def test_overview_input_when_no_dates_then_defaults_last_30d():
    # Arrange
    raw = {}

    # Act
    parsed = OverviewInput.model_validate(raw)

    # Assert
    today = date.today()
    assert parsed.date_to == today
    assert parsed.date_from == today - timedelta(days=30)
```

## 3. `conftest.py` raiz (unit)

`tests/conftest.py`:

```python
"""Conftest unit del Lambda analytics.

- Setea env vars que el Lambda necesita en runtime (sin valores reales).
- Agrega core/ al sys.path.
- Provee fixtures de mocking para shared.db, shared.cache, shared.rate_limit.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# 1. sys.path: agregar core/ Y shared/ resolvible
_LAMBDA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_LAMBDA_ROOT))
sys.path.insert(0, str(_LAMBDA_ROOT.parent.parent / 'shared'))  # dev sin vendoring


# 2. Env vars de runtime
os.environ.setdefault('LOG_LEVEL', 'DEBUG')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'analytics-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'Portfolio/AnalyticsTest')
os.environ.setdefault('CORS_ALLOWED_ORIGINS', '*')
os.environ.setdefault('RATE_LIMIT_ENDPOINT', '/analytics')


# 3. Mocks compartidos
@pytest.fixture
def mock_db_session(mocker):
    """Mockea shared.db.db_session como context manager que devuelve un MagicMock."""
    session = MagicMock(name='SQLAlchemySession')
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = None
    mocker.patch('shared.db.db_session', return_value=cm)
    return session


@pytest.fixture
def mock_check_or_raise(mocker):
    """Mockea shared.rate_limit.check_or_raise (no-op por default)."""
    return mocker.patch('shared.rate_limit.check_or_raise', return_value=None)


@pytest.fixture
def no_cache(mocker):
    """Convierte @cached en passthrough — testea el computo real, no la shell."""
    def _passthrough(**_dec_kwargs):
        def _wrap(fn):
            return fn
        return _wrap
    mocker.patch('shared.cache.cached', side_effect=_passthrough)
```

## 4. `conftest.py` integration

`tests/integration/conftest.py`:

```python
"""Conftest integration: tests E2E contra Neon test branch + DynamoDB test tables.

REQUIERE:
- AWS_PROFILE configurado (tfs-dev)
- DB_URL en docker/env/server/.dev apuntando al branch test
- Tablas DynamoDB `portfolio-cache-dev`, `portfolio-rate-limit-*-dev` existentes
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest


_LAMBDA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_LAMBDA_ROOT / 'core'))


@pytest.fixture(scope='session')
def db_url() -> str:
    """Resuelve DB_URL leyendo solo la key del .env (NUNCA volcarlo entero)."""
    import subprocess
    result = subprocess.run(
        ['grep', '-m1', '^DB_URL=', 'docker/env/server/.dev'],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip().split('=', 1)[1]


@pytest.fixture(autouse=True)
def _isolate_cache_namespace(monkeypatch):
    """Cada test corre con un namespace de cache aislado para no colisionar."""
    test_ns = f'analytics-test-{uuid.uuid4().hex[:8]}'
    monkeypatch.setenv('CACHE_NAMESPACE_PREFIX', test_ns)
    yield
    # cleanup: borrar items del cache con ese prefix
    # (implementacion: scan + batch_delete via shared.cache.invalidate_namespace)
```

## 5. Tests obligatorios por capa

### 5.1 Models — minimo (por accion)

Para CADA OperationInput, 4 tests minimo:

| Archivo | Escenario |
|---------|-----------|
| `test_<X>_input_when_valid_then_returns_parsed.py` | Happy path |
| `test_<X>_input_when_no_dates_then_defaults_last_30d.py` | Defaults |
| `test_<X>_input_when_range_over_90d_then_raises.py` | AC-3 |
| `test_<X>_input_when_invalid_field_then_raises.py` | Validacion campo (segun accion) |

Para acciones con paginacion (events/list, sessions/list, visits/list,
contacts/list) sumar:

| Archivo | Escenario |
|---------|-----------|
| `test_<X>_input_when_page_size_over_max_then_raises.py` | AC-10 |
| `test_<X>_input_when_page_zero_then_raises.py` | page >= 1 |

### 5.2 Services — minimo (por funcion)

Para cada service function, 3 tests minimo:

| Archivo | Escenario |
|---------|-----------|
| `test_<service>_<action>_when_data_then_returns_shape.py` | Happy path con mock data |
| `test_<service>_<action>_when_empty_db_then_zeros.py` | Edge: DB sin filas |
| `test_<service>_<action>_when_db_error_then_raises_service_error.py` | Error handling |

Mocking pattern:

```python
def test_overview_when_data_then_returns_shape(mock_db_session, no_cache):
    # Arrange: hacer que cada scalar() devuelva un valor distinto en orden
    mock_db_session.scalar.side_effect = [
        100,   # sessions
        80,    # visits
        500,   # events
        5,     # contacts
        75,    # unique_visitors
        45.5,  # avg_visit_duration
        12,    # bounce_visits
    ]
    from datetime import date
    from core.services.analytics_service import overview

    # Act
    result = overview(date_from=date(2026, 4, 27), date_to=date(2026, 5, 27))

    # Assert
    assert result == {
        'sessions': 100, 'visits': 80, 'events': 500, 'contacts': 5,
        'unique_visitors': 75, 'avg_visit_duration_sec': 45.5,
        'bounce_rate': 0.15,  # 12/80
        'from': '2026-04-27', 'to': '2026-05-27',
    }
```

### 5.3 Controllers — minimo

Para cada controller, 3 tests:

| Archivo | Escenario |
|---------|-----------|
| `test_<action>_controller_when_valid_then_calls_service_and_returns_ok.py` | Happy path |
| `test_<action>_controller_when_rate_limited_then_raises.py` | AC-5 / guard delega |
| `test_<action>_controller_when_blacklisted_then_raises.py` | AC-6 |

### 5.4 Handler — minimo

| Archivo | Escenario |
|---------|-----------|
| `test_handler_when_known_operation_then_dispatches.py` | Routing |
| `test_handler_when_unknown_operation_then_returns_400.py` | AC-4 |
| `test_handler_when_get_with_query_params_then_extracts_data.py` | GET parsing |
| `test_handler_when_options_then_returns_cors_headers.py` | preflight (si aplica) |

### 5.5 Integration — flujos seleccionados

NO se prueba cada combinacion. Solo flujos representativos:

| Archivo | Escenario | AC |
|---------|-----------|----|
| `test_overview_e2e_happy_path.py` | GET overview con dates -> 200 + shape | AC-1, AC-2 |
| `test_overview_e2e_range_too_wide.py` | from/to > 90d -> 400 | AC-3 |
| `test_rate_limit_e2e_block_after_10_requests.py` | 11 requests/min -> 429 | AC-5 |
| `test_sessions_detail_e2e_not_found.py` | session_id inexistente -> 404 | AC-11 |
| `test_cache_e2e_hit_returns_same_data.py` | 2 requests -> 2da hit | AC-8 |
| `test_funnel_e2e_with_seeded_data.py` | seed sessions+visits+contacts -> rates | AC-15 |

## 6. Coverage

Threshold: **80% per-file en `core/`**. Enforced por `serverless tests
--type=coverage --lambda=analytics`.

Archivos que deben llegar al 80%:

- `core/handler.py`
- `core/settings/config.py`
- `core/settings/operations.py`
- `core/models/_common.py`
- `core/models/<dominio>.py` (8 archivos)
- `core/controllers/<dominio>/<action>.py` (19 archivos)
- `core/services/<dominio>_service.py` (8 archivos)
- `core/utils/rate_limit_guard.py`

Total archivos: ~40. Cada uno con su test mirror.

Comando:

```bash
python devtools/run.py serverless tests --type=coverage --lambda=analytics
```

## 7. Asserts EXACTOS

Regla del repo: NUNCA asserts vagos. Ejemplos:

```python
# MAL
assert result['sessions'] > 0
assert 'sessions' in result
assert isinstance(result, dict)

# BIEN
assert result['sessions'] == 100
assert list(result.keys()) == ['sessions', 'visits', 'events', 'contacts',
                               'unique_visitors', 'avg_visit_duration_sec',
                               'bounce_rate', 'from', 'to']
```

Si el valor es no-determinista (un timestamp, un UUID), usar mocking
para fijarlo:

```python
mocker.patch('core.services.analytics_service.datetime')\
      .utcnow.return_value = datetime(2026, 5, 27, 14, 0, 0)
```

## 8. Property-based testing (Hypothesis)

Solo donde aporta valor — validators puros, parsing de fechas. Ejemplos:

```python
# tests/unit/models/test_date_range_property.py
"""
Property: para cualquier rango (from, to) con span <= 90d,
DateRange.model_validate no lanza.
"""
from datetime import date, timedelta
from hypothesis import given, strategies as st

from core.models._common import DateRange


@given(
    days_back=st.integers(min_value=0, max_value=90),
    span_days=st.integers(min_value=0, max_value=90),
)
def test_date_range_property_span_under_90d_never_raises(days_back, span_days):
    if days_back + span_days > 365:  # solo rangos del ultimo year
        return
    today = date.today()
    date_to = today - timedelta(days=days_back)
    date_from = date_to - timedelta(days=span_days)

    parsed = DateRange.model_validate({'from': date_from.isoformat(), 'to': date_to.isoformat()})

    assert parsed.date_from == date_from
    assert parsed.date_to == date_to
```

## 9. Testing del cache (integration)

Test del flujo de cache hit:

```python
# tests/integration/test_cache_e2e_hit_returns_same_data.py
"""
Given el cache vacio,
When llega el primer GET overview,
Then la respuesta se computa y se guarda.
When llega un segundo GET overview identico dentro de 60s,
Then la respuesta viene del cache (mismo body).
"""
def test_cache_overview_hit(_clean_cache):
    from core.handler import lambda_handler

    event = _build_event('analytics', 'overview', from_='2026-04-27', to='2026-05-27')

    # Act 1: cache miss
    resp1 = lambda_handler(event, None)
    body1 = json.loads(resp1['body'])

    # Act 2: cache hit (segundo request identico)
    resp2 = lambda_handler(event, None)
    body2 = json.loads(resp2['body'])

    # Assert: misma data
    assert body1['data'] == body2['data']
    # Assert: la segunda fue cache hit (verificable via logs o cuenta de SQL queries
    # con sqlalchemy event listener)
```

## 10. Smoke tests post-deploy

NO van en `tests/` (no son automaticos). Son comandos curl que se corren
manualmente tras deploy a dev/stage/prod. Estan en
[11-verificacion-e2e.md](11-verificacion-e2e.md).

## 11. Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Multiples `test_*` en el mismo archivo | Rompe el estandar | Un archivo por escenario |
| Mockear el controller en su propio test | Test que no prueba nada | Mockear solo el service + check_or_raise |
| Mockear el service en su propio test | Idem | Mockear solo `db_session` |
| `assert result is not None` | Vago | `assert result == {...}` |
| Tests integration que fallan si la DB esta lenta | Flaky | Timeouts explicitos + retry con backoff |
| Tests integration que dejan basura en el cache | Cross-test pollution | Namespace aislado por test |
| Cachear los kwargs con `mock_db_session` | El mock no es serializable | Pass `no_cache` fixture |
| Hardcodear `date.today()` | Test flaky cuando cruza medianoche | Mock `date.today()` o usar `freezegun` |

[< 05-cache-layer](05-cache-layer.md) | [Siguiente: 07-archivos-afectados >](07-archivos-afectados.md)
