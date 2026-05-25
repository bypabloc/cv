"""Builders de integration para sustituir el engine SQLAlchemy.

Prefijo `_` para que pytest NO recolecte este archivo como tests.

`run_tables` del service construye un engine SQLAlchemy real con
`sqlalchemy.create_engine` y consulta `pg_stat_user_tables`. En los
integration tests sin un PostgreSQL en vivo se reemplaza ese engine por
un doble que devuelve filas configurables, manteniendo el resto del flujo
(handler -> controller Tables -> run_tables) sin mockear.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock


def fake_engine_with_rows(rows: list[tuple[str, int]]) -> MagicMock:
    """Construye un engine SQLAlchemy falso que devuelve `rows`.

    Parameters
    ----------
    rows
        Pares (table_name, estimated_rows) que la query simulada
        `pg_stat_user_tables` devuelve, en orden.

    Returns
    -------
    MagicMock
        Un objeto compatible con la API que usa `run_tables`:
        `engine.connect()` como context manager -> `conn.execute(...).all()`.
    """
    result_rows = [
        SimpleNamespace(table_name=name, estimated_rows=count)
        for name, count in rows
    ]
    conn = MagicMock()
    conn.execute.return_value.all.return_value = result_rows
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    return engine


def failing_engine(message: str) -> MagicMock:
    """Construye un engine SQLAlchemy falso cuya conexion falla.

    `engine.connect()` lanza una excepcion al usarse como context manager,
    simulando una DB inaccesible o un schema sin migrar.
    """
    engine = MagicMock()
    engine.connect.side_effect = RuntimeError(message)
    return engine


def raise_on_create(_url: str, **_kwargs: Any) -> MagicMock:
    """side_effect para create_engine que falla al construir el engine."""
    raise RuntimeError('no se pudo construir el engine')
