"""Configuracion pytest de los integration tests del Lambda `db`.

Los integration tests del Lambda `db` invocan `lambda_handler` REAL con el
evento crudo `{command, args}` y ejercitan el flujo completo
handler -> validate_event -> import_controller -> controller -> service.

A diferencia del estandar de integration "contra recursos AWS reales",
estos tests NO necesitan una cuenta AWS ni un PostgreSQL Neon en vivo:
el unico recurso externo del Lambda `db` es PostgreSQL via Alembic. Se
sustituye con fidelidad alta — se mockea SOLO la frontera de E/S
(`alembic.command.*` y `sqlalchemy.create_engine`), de modo que TODO el
codigo propio del Lambda (routing del handler, validacion del evento,
resolucion dinamica del controller, ciclo preload/validate/execute, y la
logica del service) corre sin mockear. El objetivo es que
`serverless tests --type=integration --lambda=db` corra y pase en CI y en
local sin infraestructura.

Setea las env vars minimas que `AppConfig` necesita y `DATABASE_URL` con
un valor sintetico — asi `ensure_database_url` es un no-op (respeta la
`DATABASE_URL` del entorno) sin necesidad de mockearla.
"""

import os
import sys
from pathlib import Path

import pytest

# core/ al path: imports absolutos del codigo del Lambda (handler,
# controllers., services., models., settings., utils.).
_LAMBDA_ROOT = Path(__file__).resolve().parent.parent
_CORE = _LAMBDA_ROOT / 'core'
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

# Fallback para `import shared...` si no esta vendorizado en core/shared/.
if not (_CORE / 'shared').is_dir():
    _LAMBDA_BASE = _LAMBDA_ROOT.parents[1]
    if str(_LAMBDA_BASE) not in sys.path:
        sys.path.insert(0, str(_LAMBDA_BASE))

# Env vars minimas para que AppConfig cargue sin un entorno Lambda real.
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('SSM_NEON_URL_PATH', '/portfolio/dev/neon-url')
os.environ.setdefault('POWERTOOLS_SERVICE_NAME', 'db-test')
os.environ.setdefault('POWERTOOLS_METRICS_NAMESPACE', 'PortfolioTest')
# DATABASE_URL sintetica: ensure_database_url la respeta -> no-op real.
os.environ.setdefault(
    'DATABASE_URL', 'postgresql://itest:itest@localhost:5432/itest'
)


@pytest.fixture
def alembic_recorder(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Sustituye la frontera Alembic <-> PostgreSQL del service `db`.

    Reemplaza `alembic.command.{upgrade,downgrade,stamp,current,history}`
    por funciones que registran sus llamadas y, para `current`/`history`,
    escriben en el buffer del `Config` la salida configurada. Devuelve un
    dict mutable con:
      - `calls`     : lista de (comando, target) en orden de invocacion.
      - `revision`  : lo que `command.current` escribe en el buffer.
      - `history`   : lo que `command.history` escribe en el buffer.

    El test ajusta `revision`/`history` ANTES de invocar el handler.
    """
    from services import db_service

    state: dict = {
        'calls': [],
        'revision': '81c2cc51db34',
        'history': 'rev0 -> 81c2cc51db34 (head)',
    }

    def _record(name: str):
        def _fn(_cfg: object, target: str = 'head', **_kwargs: object) -> None:
            state['calls'].append((name, target))

        return _fn

    def _current(cfg: object, **_kwargs: object) -> None:
        state['calls'].append(('current', None))
        if state['revision']:
            cfg.stdout.write(state['revision'])

    def _history(cfg: object, **_kwargs: object) -> None:
        state['calls'].append(('history', None))
        if state['history']:
            cfg.stdout.write(state['history'])

    monkeypatch.setattr(db_service.command, 'upgrade', _record('upgrade'))
    monkeypatch.setattr(db_service.command, 'downgrade', _record('downgrade'))
    monkeypatch.setattr(db_service.command, 'stamp', _record('stamp'))
    monkeypatch.setattr(db_service.command, 'current', _current)
    monkeypatch.setattr(db_service.command, 'history', _history)

    return state
