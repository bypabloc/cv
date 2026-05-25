"""shared.db.repository.ensure_session_and_visit — SELECT guardia.

Given una Session,
When ensure_session_and_visit ejecuta el SELECT FOR UPDATE del ultimo
     visit del session,
Then el statement compila a un SELECT FROM `vis_session_visits` con
     `host(ip)`, ORDER BY started_at DESC LIMIT 1 FOR UPDATE.

Guardia anti-regresion: el SELECT estaba en raw SQL previamente; al
renombrarse la tabla podia quedar apuntando al nombre viejo. Ahora va
por ORM (`select(SessionVisit.visit_id, ...)`) — el `__tablename__`
del modelo es la unica fuente de verdad.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repository import ensure_session_and_visit
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import Select

pytestmark = pytest.mark.unit


def test_ensure_session_and_visit_select_targets_vis_session_visits() -> None:
    # Arrange — visit previo None, foco esta en la query del SELECT
    session = MagicMock()
    session.execute.return_value.first.return_value = None
    session.flush.side_effect = lambda: setattr(
        session.add.call_args[0][0], 'visit_id', 'fake-uuid'
    )

    # Act
    ensure_session_and_visit(
        session,
        session_id='sess-abc',
        ip='1.2.3.4',
        country=None,
        user_agent=None,
        browser=None,
        browser_version=None,
        os_name=None,
        device_type=None,
        utm_source=None,
        utm_medium=None,
        utm_campaign=None,
        utm_content=None,
        utm_term=None,
        referrer=None,
        landing_page_path=None,
        niche=None,
        bump_event_count=True,
    )

    # Assert — el segundo execute es el SELECT FOR UPDATE
    select_stmt = session.execute.call_args_list[1][0][0]
    assert isinstance(select_stmt, Select), (
        f'esperaba Select, recibi {type(select_stmt)}'
    )
    compiled = str(
        select_stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={'literal_binds': True},
        )
    )
    assert 'FROM vis_session_visits' in compiled, compiled
    assert 'host(vis_session_visits.ip)' in compiled
    assert 'ORDER BY vis_session_visits.started_at DESC' in compiled
    assert 'LIMIT 1' in compiled
    assert 'FOR UPDATE' in compiled
    # session_id literal viene como string en literal_binds
    assert "'sess-abc'" in compiled
