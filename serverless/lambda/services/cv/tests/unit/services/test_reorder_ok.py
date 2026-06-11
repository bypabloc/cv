"""reorder reescribe las prioridades del niche en el orden recibido.

Given un niche existente con 2 experiences asignadas,
When se invoca reorder con ordered_slugs == el conjunto exacto,
Then llama reorder_niche_priorities con los ids EN ORDEN e invalida el
cache tag 'cv'.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_reorder_ok(monkeypatch):
    from services import content_service, reorder_service

    fake_session = MagicMock()
    # 1a query: niche id; 2a query: filas (slug, id) del niche.
    niche_result = MagicMock()
    niche_result.scalar_one_or_none.return_value = 'niche-1'
    rows_result = MagicMock()
    rows_result.all.return_value = [('exp-a', 'id-a'), ('exp-b', 'id-b')]
    fake_session.execute.side_effect = [niche_result, rows_result]
    monkeypatch.setattr(
        reorder_service, 'db_session', lambda: _ctx(fake_session),
    )
    reorder_mock = MagicMock()
    monkeypatch.setattr(
        reorder_service, 'reorder_niche_priorities', reorder_mock,
    )
    cache = MagicMock()
    monkeypatch.setattr(content_service, 'DynamoDBCache', lambda: cache)

    result = reorder_service.reorder(
        entity_type='experience',
        niche='generic',
        ordered_slugs=['exp-b', 'exp-a'],
    )

    assert result == {
        'entity_type': 'experience',
        'niche': 'generic',
        'reordered': 2,
    }
    reorder_mock.assert_called_once_with(
        fake_session, 'experience', 'niche-1', ['id-b', 'id-a'],
    )
    cache.invalidate.assert_called_once_with(tag='cv')
