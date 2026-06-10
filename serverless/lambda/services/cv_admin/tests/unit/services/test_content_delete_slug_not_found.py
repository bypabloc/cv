"""delete_entity de un slug inexistente -> 4404 SLUG_NOT_FOUND.

Given un slug que no existe (el delete devuelve False),
When se invoca content_service.delete_entity,
Then ServiceError 4404 SLUG_NOT_FOUND y el cache NO se invalida.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest


@contextmanager
def _ctx(session):
    yield session


def test_content_delete_slug_not_found(monkeypatch):
    from services import content_service
    from services._errors import ServiceError
    import shared.db.repositories.cv_write_entities as cv_write_entities

    monkeypatch.setattr(
        content_service, 'db_session', lambda: _ctx(MagicMock()),
    )
    monkeypatch.setattr(
        cv_write_entities, 'delete_project', MagicMock(return_value=False),
    )
    cache = MagicMock()
    monkeypatch.setattr(content_service, 'DynamoDBCache', lambda: cache)

    with pytest.raises(ServiceError) as exc:
        content_service.delete_entity(entity='project', slug='no-existe')

    assert exc.value.code == 4404
    assert exc.value.error_code == 'SLUG_NOT_FOUND'
    cache.invalidate.assert_not_called()
