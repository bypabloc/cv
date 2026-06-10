"""delete_entity usa el delete dedicado para experience/project/skill_cat.

Given un slug existente de experience,
When se invoca content_service.delete_entity,
Then llama delete_experience, devuelve {entity, deleted} e invalida el
cache tag 'cv'.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_content_delete_dedicated_ok(monkeypatch):
    from services import content_service
    from shared.db.repositories import cv_write_entities

    fake_session = MagicMock()
    monkeypatch.setattr(
        content_service, 'db_session', lambda: _ctx(fake_session),
    )
    delete_mock = MagicMock(return_value=True)
    monkeypatch.setattr(cv_write_entities, 'delete_experience', delete_mock)
    cache = MagicMock()
    monkeypatch.setattr(content_service, 'DynamoDBCache', lambda: cache)

    result = content_service.delete_entity(
        entity='experience', slug='smoke-exp',
    )

    assert result == {'entity': 'smoke-exp', 'deleted': True}
    delete_mock.assert_called_once_with(fake_session, 'smoke-exp')
    cache.invalidate.assert_called_once_with(tag='cv')
