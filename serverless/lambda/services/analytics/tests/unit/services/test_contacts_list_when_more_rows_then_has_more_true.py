"""
Given total=120 contactos y una pagina de 50 (offset 0) con 50 filas,
When se invoca contacts_service.list (NO cacheado, llamada directa),
Then devuelve el shape de paginacion con has_more=True y el id como str.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import services.contacts_service as contacts_service


def test_contacts_list_when_more_rows_then_has_more_true(mocker):
    # Arrange: 50 filas identicas + total 120 -> has_more = (0+50) < 120.
    created = datetime(2026, 5, 1, 10, 30, tzinfo=UTC)
    row = MagicMock(name='ContactRow')
    row.id = '11111111-2222-3333-4444-555555555555'
    row.created_at = created
    row.name = 'Ada Lovelace'
    row.email = 'ada@example.com'
    row.message = 'Hola, me interesa colaborar'
    row.company = 'Analytical Engines'
    row.role = 'CTO'
    row.service_type = 'consulting'
    row.budget = '10k-50k'
    row.timeline = 'Q3'
    row.niche = 'fintech'
    row.status = 'new'
    row.session_id = 's-1'

    session = MagicMock(name='SQLAlchemySession')
    session.scalar.return_value = 120
    session.execute.return_value.all.return_value = [row] * 50
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(contacts_service, 'db_session', return_value=cm)

    # Act
    result = contacts_service.list(
        date_from=datetime(2026, 4, 27).date(),
        date_to=datetime(2026, 5, 28).date(),
        page=1,
        page_size=50,
        offset=0,
        status='new',
    )

    # Assert: shape de paginacion exacto + id como str.
    assert result['page'] == 1
    assert result['page_size'] == 50
    assert result['total'] == 120
    assert result['has_more'] is True
    assert len(result['items']) == 50
    assert result['items'][0] == {
        'id': '11111111-2222-3333-4444-555555555555',
        'created_at': '2026-05-01T10:30:00+00:00',
        'name': 'Ada Lovelace',
        'email': 'ada@example.com',
        'message': 'Hola, me interesa colaborar',
        'company': 'Analytical Engines',
        'role': 'CTO',
        'service_type': 'consulting',
        'budget': '10k-50k',
        'timeline': 'Q3',
        'niche': 'fintech',
        'status': 'new',
        'session_id': 's-1',
    }
