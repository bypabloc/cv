"""shared.db.repository.ensure_session_and_visit — UPSERT guardia.

Given una Session,
When ensure_session_and_visit ejecuta el UPSERT inicial sobre
     `vis_sessions`,
Then el statement compila a un INSERT ... ON CONFLICT (session_id)
     DO UPDATE SET last_seen_at = now() usando `sa_func.now()` (no
     `text('now()')`).

Guardia anti-regresion del cleanup de raw SQL: antes la clausula `SET`
del ON CONFLICT venia como `text('now()')`. Migrarla a `sa_func.now()`
deja el statement 100% Core y elimina otra fuente de strings sueltos.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.models.visitor.session import Session as SessionRow
from shared.db.repository import ensure_session_and_visit
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import Insert as PgInsert

pytestmark = pytest.mark.unit


def test_ensure_session_and_visit_upsert_targets_vis_sessions_with_now() -> (
    None
):
    # Arrange — visit previo None, foco esta en el primer execute (UPSERT)
    session = MagicMock()
    session.execute.return_value.first.return_value = None
    session.flush.side_effect = lambda: setattr(
        session.add.call_args[0][0], 'visit_id', 'fake-uuid'
    )

    # Act
    ensure_session_and_visit(
        session,
        session_id='sess-xyz',
        ip='1.2.3.4',
        country=None,
        user_agent='ua',
        browser='Chrome',
        browser_version='120',
        os_name='Linux',
        device_type='desktop',
        utm_source=None,
        utm_medium=None,
        utm_campaign=None,
        utm_content=None,
        utm_term=None,
        referrer=None,
        landing_page_path=None,
        niche=None,
    )

    # Assert — el primer execute es el INSERT ON CONFLICT
    upsert_stmt = session.execute.call_args_list[0][0][0]
    assert isinstance(upsert_stmt, PgInsert), (
        f'esperaba postgresql.Insert, recibi {type(upsert_stmt)}'
    )
    compiled = str(
        upsert_stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={'literal_binds': True},
        )
    )
    assert SessionRow.__tablename__ == 'vis_sessions'
    assert 'INSERT INTO vis_sessions' in compiled, compiled
    assert 'ON CONFLICT (session_id) DO UPDATE' in compiled
    assert 'last_seen_at = now()' in compiled
