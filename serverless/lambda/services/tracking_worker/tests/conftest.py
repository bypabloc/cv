"""Configuracion pytest del Lambda `tracking_worker`.

Agrega `core/` al `sys.path` para que los imports absolutos del codigo
(`handler`, `controllers.`, `services.`, `models.`, `settings.`)
resuelvan en los tests.

La libreria comun `shared/` normalmente se vendoriza en `core/shared/`
por devtools antes de correr los tests (`serverless tests --type=unit`
lo hace). Si no esta vendorizada (pytest invocado directo), este
conftest agrega `serverless/lambda/` al path como fallback para que
`import shared...` resuelva desde la fuente maestra.

Setea las env vars minimas que `AppConfig` (settings/config.py) y las
libs de `shared/` necesitan, y mockea AWS para los tests unit (moto).
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# core/ al path: imports absolutos del codigo del Lambda.
_LAMBDA_ROOT = Path(__file__).resolve().parent.parent
_CORE = _LAMBDA_ROOT / 'core'
sys.path.insert(0, str(_CORE))

# Fallback para `import shared...` si no esta vendorizado en core/shared/.
# La fuente maestra shared/ vive en serverless/lambda/ (parents[1]:
# <lambda>/ -> services/ -> lambda/).
if not (_CORE / 'shared').is_dir():
    _LAMBDA_BASE = _LAMBDA_ROOT.parents[1]
    sys.path.insert(0, str(_LAMBDA_BASE))

# Env vars minimas para que AppConfig + shared.* carguen sin un
# entorno Lambda real. Se setean al import del conftest, antes de
# cualquier test.
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('STAGE', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('LOG_LEVEL', 'INFO')
# DATABASE_URL: requerido por shared.db.url.resolve_database_url. En
# unit tests reales NUNCA conectamos: mockeamos db_session via fixture.
os.environ.setdefault(
    'DATABASE_URL',
    'postgresql://test:test@localhost/test',
)
os.environ.setdefault('CACHE_TABLE_NAME', 'portfolio-cache-test')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'tracking-worker-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setea AWS credentials fake en todos los tests (autouse).

    Previene que boto3 lea ~/.aws/credentials reales o intente STS.
    Necesario para que moto interceptee las llamadas si se activa.
    """
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')


_STUB_VISIT_ID = '019e5c50-0000-7000-8000-000000000aaa'
"""visit_id determinista (UUIDv7 valido) que el mock de
`ensure_session_and_visit` retorna. Lo usan asserts de tests."""


@pytest.fixture
def session_visit_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Captura los kwargs de cada invocacion a `ensure_session_and_visit`.

    Retorna `(session_id, _STUB_VISIT_ID)` para que los asserts de
    tests downstream sean predecibles. Mockea el helper en
    `services.persistence` (donde se importa).
    """
    captured: list[dict] = []

    def _fake_ensure(_session: object, **kwargs: object) -> tuple[str, str]:
        captured.append(dict(kwargs))
        return str(kwargs['session_id']), _STUB_VISIT_ID

    monkeypatch.setattr(
        'services.persistence.ensure_session_and_visit',
        _fake_ensure,
    )
    return captured


@pytest.fixture
def insert_tracking_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> list[dict]:
    """Captura los payloads de `insert_tracking_idempotent`.

    Devuelve True por default (fila insertada). Tests que quieran
    simular conflicto (rowcount==0) pueden re-monkeypatch despues con
    `lambda *_a, **_k: False`.
    """
    captured: list[dict] = []

    def _fake_insert(_session: object, payload: dict) -> bool:
        captured.append(payload)
        return True

    monkeypatch.setattr(
        'services.persistence.insert_tracking_idempotent',
        _fake_insert,
    )
    return captured


@pytest.fixture
def db_session_calls(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Mockea `db_session()` para registrar cuantas veces se invoco.

    Retorna una lista append-only: cada entrada es un timestamp
    monotonico del momento en que se entro al context manager. Asi
    los tests pueden afirmar `len(calls) == 1` para validar que el
    batch comparte una unica session.

    El object yielded soporta `.begin_nested()` como context manager
    (no-op): el service usa `session.begin_nested()` para aislar
    cada mensaje con un savepoint Postgres.
    """
    from contextlib import contextmanager

    calls: list[int] = []

    class _FakeSession:
        def begin_nested(self):
            @contextmanager
            def _cm():
                yield None

            return _cm()

    @contextmanager
    def _fake_db_session() -> Generator[_FakeSession]:
        calls.append(len(calls) + 1)
        yield _FakeSession()

    monkeypatch.setattr(
        'controllers.worker.process_batch.db_session',
        _fake_db_session,
    )
    return calls


@pytest.fixture
def patch_parse_user_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reemplaza `parse_user_agent` por un stub determinista.

    Evita dependencia del cache @cached (DynamoDB) y del regex spec
    de ua-parser. Los tests del controller no validan el parsing del
    UA — eso es responsabilidad de tests del service.
    """

    def _fake_parse(_user_agent: str | None) -> dict[str, str]:
        return {
            'browser': 'Chrome',
            'browser_version': '118',
            'os': 'Linux',
            'device_type': 'desktop',
        }

    monkeypatch.setattr(
        'services.persistence.parse_user_agent',
        _fake_parse,
    )
