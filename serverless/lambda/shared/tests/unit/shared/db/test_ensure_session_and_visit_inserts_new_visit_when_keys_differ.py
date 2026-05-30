"""shared.db.repository.ensure_session_and_visit — INSERT branch.

Given una Session sin visit previo (`first()` devuelve None),
When se invoca ensure_session_and_visit,
Then agrega un nuevo `SessionVisit` con todos los campos del payload,
     hace flush para obtener el `visit_id`, y NO ejecuta UPDATE.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest
from shared.db.models.visitor.session_visit import SessionVisit
from shared.db.repository import ensure_session_and_visit

pytestmark = pytest.mark.unit


def test_ensure_session_and_visit_inserts_new_visit_when_keys_differ() -> None:
    # Arrange — session sin visit previo
    session = MagicMock()
    session.execute.return_value.first.return_value = None

    # Patch session.add para capturar el SessionVisit y poblar visit_id
    # cuando flush() lo simulando el server-side default.
    added_objects: list[SessionVisit] = []

    def fake_add(obj: SessionVisit) -> None:
        added_objects.append(obj)

    def fake_flush() -> None:
        # uuidv7 simulado para que str(new_visit.visit_id) no falle.
        added_objects[0].visit_id = UUID('019e5fce-385d-7530-8f6e-8e17df16f08a')

    session.add.side_effect = fake_add
    session.flush.side_effect = fake_flush

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

    # Assert
    assert session_id_ret == 'sess-abc'
    assert visit_id == '019e5fce-385d-7530-8f6e-8e17df16f08a'
    # session.execute se llamo dos veces: UPSERT sessions + SELECT visit
    assert session.execute.call_count == 2
    # Solo 1 add: el SessionVisit nuevo
    assert len(added_objects) == 1
    new_visit = added_objects[0]
    assert isinstance(new_visit, SessionVisit)
    assert new_visit.session_id == 'sess-abc'
    assert new_visit.ip == '1.2.3.4'
    assert new_visit.country == 'CL'
    assert new_visit.utm_source == 'google'
    assert new_visit.utm_medium == 'cpc'
    assert new_visit.utm_campaign == 'launch'
    assert new_visit.utm_content is None
    assert new_visit.utm_term is None
    assert new_visit.referrer == 'https://example.com'
    assert new_visit.landing_page_path == '/'
    assert new_visit.niche == 'fintech'
    assert new_visit.event_count == 1
    # flush emitido para obtener visit_id server-side
    assert session.flush.call_count == 1
