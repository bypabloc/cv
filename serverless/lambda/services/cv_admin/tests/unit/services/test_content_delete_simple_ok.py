"""delete_entity delega en delete_simple para las entidades simples.

Given un slug existente de certificate,
When se invoca content_service.delete_entity,
Then llama delete_simple(session, 'certificate', slug) e invalida.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_content_delete_simple_ok(monkeypatch):
    from services import content_service
    import shared.db.repositories.cv_write_entities as cv_write_entities

    fake_session = MagicMock()
    monkeypatch.setattr(
        content_service, 'db_session', lambda: _ctx(fake_session),
    )
    delete_mock = MagicMock(return_value=True)
    monkeypatch.setattr(cv_write_entities, 'delete_simple', delete_mock)
    cache = MagicMock()
    monkeypatch.setattr(content_service, 'DynamoDBCache', lambda: cache)

    result = content_service.delete_entity(
        entity='certificate', slug='docker-2023',
    )

    assert result == {'entity': 'docker-2023', 'deleted': True}
    delete_mock.assert_called_once_with(
        fake_session, 'certificate', 'docker-2023',
    )
    cache.invalidate.assert_called_once_with(tag='cv')
