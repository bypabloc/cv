"""upsert_entity escribe en una tx e invalida el cache tag 'cv'.

Given un payload valido de experience con niches del catalogo,
When se invoca content_service.upsert_entity,
Then llama upsert_experience con la session + niche_ids, devuelve
{entity, id} e invalida el cache tag 'cv' tras el commit.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_content_upsert_experience_ok(monkeypatch):
    from services import content_service
    import shared.db.repositories.cv_write_entities as cv_write_entities

    fake_session = MagicMock()
    monkeypatch.setattr(
        content_service, 'db_session', lambda: _ctx(fake_session),
    )
    niche_ids = {'generic': 'niche-1'}
    monkeypatch.setattr(
        content_service, 'resolve_niches', lambda _s: niche_ids,
    )
    upsert_mock = MagicMock(return_value='exp-id-1')
    monkeypatch.setattr(cv_write_entities, 'upsert_experience', upsert_mock)
    cache = MagicMock()
    monkeypatch.setattr(content_service, 'DynamoDBCache', lambda: cache)

    data = {'slug': 'smoke-exp', 'niches': ['generic'], 'priority': {}}
    result = content_service.upsert_entity(entity='experience', data=data)

    assert result == {'entity': 'smoke-exp', 'id': 'exp-id-1'}
    upsert_mock.assert_called_once_with(fake_session, data, niche_ids)
    cache.invalidate.assert_called_once_with(tag='cv')
