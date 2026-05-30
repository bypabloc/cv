"""shared.db.repository.ensure_session_and_visit — UPDATE branch.

Given una Session con un visit previo cuyas 6 claves coinciden con el
     payload entrante,
When se invoca ensure_session_and_visit con bump_event_count=True,
Then NO inserta un visit nuevo y emite un `UPDATE vis_session_visits`
     que incrementa event_count en 1 y refresca ended_at via now().

Este test guardia el bug que rompio /track en prod (commit del fix
vis_session_visits): el raw SQL usaba el nombre viejo de la tabla
(`session_visits`) y la consulta fallaba con UndefinedTable. Con ORM,
el `__tablename__` del modelo es la fuente de verdad — no hay forma
de que el nombre quede desincronizado.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from shared.db.models.visitor.session_visit import SessionVisit
from shared.db.repository import ensure_session_and_visit
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import Update

pytestmark = pytest.mark.unit


def test_ensure_session_and_visit_updates_existing_visit_when_keys_match() -> (
    None
):
    # Arrange — visit previo con las mismas 6 claves
    visit_uuid = UUID('019e5fce-385d-7530-8f6e-8e17df16f08a')
    existing_visit = SimpleNamespace(
        visit_id=visit_uuid,
        ip='1.2.3.4',
        utm_source='google',
        utm_medium='cpc',
        utm_campaign='launch',
        utm_content=None,
        utm_term=None,
    )
    session = MagicMock()
    session.execute.return_value.first.return_value = existing_visit

    # Act
    session_id_ret, visit_id = ensure_session_and_visit(
        session,
        session_id='sess-abc',
        ip='1.2.3.4',
        country='CL',
        user_agent='ua',
        browser='Chrome',
        browser_version='120',
        os_name='Linux',
        device_type='desktop',
        utm_source='google',
        utm_medium='cpc',
        utm_campaign='launch',
        utm_content=None,
        utm_term=None,
        referrer='https://example.com',
        landing_page_path='/',
        niche='fintech',
        bump_event_count=True,
    )

    # Assert — no nuevo insert
    assert session.add.call_count == 0
    assert session.flush.call_count == 0
    assert visit_id == str(visit_uuid)
    assert session_id_ret == 'sess-abc'

    # 3 execute: UPSERT sessions + SELECT visit + UPDATE visit
    assert session.execute.call_count == 3
    update_stmt = session.execute.call_args_list[2][0][0]
    assert isinstance(update_stmt, Update), (
        f'esperaba Update, recibi {type(update_stmt)}'
    )
    compiled = str(
        update_stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={'literal_binds': True},
        )
    )
    # Guardia anti-regresion: el UPDATE DEBE apuntar a la tabla con
    # prefijo `vis_` (renombrada en el squash de migraciones).
    assert 'UPDATE vis_session_visits' in compiled, compiled
    assert 'session_visits' in SessionVisit.__tablename__
    assert SessionVisit.__tablename__ == 'vis_session_visits'
    assert 'now()' in compiled
    assert 'event_count + 1' in compiled
    assert str(visit_uuid).replace('-', '') in compiled


def test_ensure_session_and_visit_skips_bump_when_flag_false() -> None:
    # Arrange — mismo visit previo, mismas keys
    visit_uuid = UUID('019e5fce-385d-7530-8f6e-8e17df16f08a')
    existing_visit = SimpleNamespace(
        visit_id=visit_uuid,
        ip='1.2.3.4',
        utm_source=None,
        utm_medium=None,
        utm_campaign=None,
        utm_content=None,
        utm_term=None,
    )
    session = MagicMock()
    session.execute.return_value.first.return_value = existing_visit

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
        bump_event_count=False,
    )

    # Assert — el UPDATE suma 0, no 1
    update_stmt = session.execute.call_args_list[2][0][0]
    compiled = str(
        update_stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={'literal_binds': True},
        )
    )
    assert 'event_count + 0' in compiled
