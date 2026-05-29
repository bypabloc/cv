"""shared.db re-exporta SQLAlchemy.

Given el subpaquete shared.db,
When importo select, func, pg_insert y Session desde shared.db,
Then son exactamente los mismos objetos que SQLAlchemy exporta y los
     services pueden usarlos sin importar sqlalchemy directo.
"""

from __future__ import annotations

import pytest
import sqlalchemy
from shared.db.sa import Session, func, pg_insert, select
from sqlalchemy.dialects.postgresql import insert as sa_pg_insert
from sqlalchemy.orm import Session as SAOrmSession

pytestmark = pytest.mark.unit


def test_select_is_sqlalchemy_select() -> None:
    # Arrange + Act + Assert
    assert select is sqlalchemy.select


def test_func_is_sqlalchemy_func() -> None:
    # Arrange + Act + Assert
    assert func is sqlalchemy.func


def test_pg_insert_is_postgresql_dialect_insert() -> None:
    # Arrange + Act + Assert
    assert pg_insert is sa_pg_insert


def test_session_is_sqlalchemy_orm_session() -> None:
    # Arrange + Act + Assert
    assert Session is SAOrmSession
