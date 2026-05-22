"""Configuracion pytest de los tests de integracion del stream_processor.

Los tests de integracion ejercitan el flujo end-to-end del Lambda:
`lambda_handler` real -> controller `Process` -> `stream_service` -> ORM
SQLAlchemy -> base de datos. Es la cobertura mas alta posible sin AWS.

Fidelidad de la base de datos
-----------------------------
El `stream_processor` persiste en Neon PostgreSQL. Correr la suite contra
un Neon real volveria los tests no ejecutables en CI (requiere red,
credenciales y un branch dedicado). Por eso la base es **SQLite
in-memory** construida a partir de los modelos SQLAlchemy reales de
`shared.db` (ver `_fixtures/db.py`): mismas tablas, mismas columnas,
mismos `NOT NULL`. Solo 3 detalles PostgreSQL-especificos se degradan
(`CITEXT`/`INET`/`JSONB` -> `TEXT`; indices con expresiones PG y
`server_default` `uuidv7()` se omiten). El `server_default` `now()` se
conserva. La columna `JSONB` (`event_props`) igual hace el roundtrip
dict<->JSON. El flujo real (handler routing, validacion del evento,
`detect_table`, `parse_*`, idempotencia, escritura ORM,
`batchItemFailures`) se ejercita completo.

Cada test obtiene una base SQLite limpia: la fixture `sqlite_db` se crea
por test (`autouse`) y el engine se descarta al terminar — no hay estado
compartido entre tests.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine

from tests.integration._fixtures.db import create_sqlite_engine


@pytest.fixture
def sqlite_db() -> Iterator[Engine]:
    """Engine SQLite in-memory con las tablas del ORM, limpio por test.

    La base vive solo mientras el test la usa; al terminar el engine se
    cierra y la base in-memory se descarta — el siguiente test arranca
    con estado limpio.
    """
    engine = create_sqlite_engine()
    try:
        yield engine
    finally:
        engine.dispose()
