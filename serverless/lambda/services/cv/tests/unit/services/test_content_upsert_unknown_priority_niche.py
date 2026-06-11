"""upsert_entity tambien valida las keys de `priority` contra el catalogo.

Given un payload con priority {'bar': 10} y bar fuera del catalogo,
When se invoca content_service.upsert_entity,
Then ServiceError 1100 UNKNOWN_NICHE con ['bar'] en detail.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest


@contextmanager
def _ctx(session):
    yield session


def test_content_upsert_unknown_priority_niche(monkeypatch):
    from services import content_service
    from services._errors import ServiceError

    monkeypatch.setattr(
        content_service, 'db_session', lambda: _ctx(MagicMock()),
    )
    monkeypatch.setattr(
        content_service, 'resolve_niches', lambda _s: {'generic': 'n1'},
    )

    data = {'slug': 's', 'niches': ['generic'], 'priority': {'bar': 10}}
    with pytest.raises(ServiceError) as exc:
        content_service.upsert_entity(entity='award', data=data)

    assert exc.value.code == 1100
    assert exc.value.detail == {'unknown_niches': ['bar']}
