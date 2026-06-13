"""upsert_entity rechaza niches fuera del catalogo ANTES de escribir.

Given un payload cuyo `niches` referencia un slug fuera del catalogo,
When se invoca content_service.upsert_entity,
Then ServiceError 1100 UNKNOWN_NICHE, el upsert NO se llama y el cache
NO se invalida.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest


@contextmanager
def _ctx(session):
    yield session


def test_content_upsert_unknown_niche(monkeypatch):
    import shared.db.repositories.cv_write_entities as cv_write_entities
    from services import content_service
    from services._errors import ServiceError

    monkeypatch.setattr(
        content_service, 'db_session', lambda: _ctx(MagicMock()),
    )
    monkeypatch.setattr(
        content_service, 'resolve_niches', lambda _s: {'generic': 'n1'},
    )
    upsert_mock = MagicMock()
    monkeypatch.setattr(cv_write_entities, 'upsert_experience', upsert_mock)
    cache = MagicMock()
    monkeypatch.setattr(content_service, 'DynamoDBCache', lambda: cache)

    data = {'slug': 's', 'niches': ['foo'], 'priority': {}}
    with pytest.raises(ServiceError) as exc:
        content_service.upsert_entity(entity='experience', data=data)

    assert exc.value.code == 1100
    assert exc.value.error_code == 'UNKNOWN_NICHE'
    assert exc.value.detail == {'unknown_niches': ['foo']}
    upsert_mock.assert_not_called()
    cache.invalidate.assert_not_called()
