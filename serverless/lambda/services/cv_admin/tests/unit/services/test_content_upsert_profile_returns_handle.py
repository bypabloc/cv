"""upsert_entity de profile usa handle como clave natural en la salida.

Given el payload del profile singleton,
When se invoca content_service.upsert_entity(entity='profile'),
Then devuelve {'entity': <handle>, 'id': <id>}.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_content_upsert_profile_returns_handle(monkeypatch):
    from services import content_service
    from shared.db.repositories import cv_write_entities

    monkeypatch.setattr(
        content_service, 'db_session', lambda: _ctx(MagicMock()),
    )
    monkeypatch.setattr(
        content_service, 'resolve_niches', lambda _s: {'generic': 'n1'},
    )
    monkeypatch.setattr(
        cv_write_entities,
        'upsert_profile',
        MagicMock(return_value='profile-id-1'),
    )
    monkeypatch.setattr(content_service, 'DynamoDBCache', MagicMock)

    data = {'handle': 'bypabloc', 'niches': ['generic']}
    result = content_service.upsert_entity(entity='profile', data=data)

    assert result == {'entity': 'bypabloc', 'id': 'profile-id-1'}
