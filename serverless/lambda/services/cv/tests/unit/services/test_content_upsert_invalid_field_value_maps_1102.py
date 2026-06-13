"""upsert_entity traduce un ValueError del upsert a ServiceError 1102.

Given un payload cuyo shape pasa el modelo pero cuyo valor revienta la
coercion del repositorio (ej. una fecha 'YYYY-13' que hace que
coerce_date lance ValueError),
When se invoca content_service.upsert_entity,
Then el ValueError NO escapa como 500 unhandled: se traduce a
ServiceError code=1102 / error_code=INVALID_FIELD_VALUE (400 de
contrato via _CODE_TO_STATUS del controller).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest


@contextmanager
def _ctx(session):
    yield session


def test_content_upsert_invalid_field_value_maps_1102(monkeypatch):
    import shared.db.repositories.cv_write_entities as cv_write_entities
    from services import content_service
    from services._errors import ServiceError

    fake_session = MagicMock()
    monkeypatch.setattr(
        content_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        content_service, 'resolve_niches', lambda _s: {'generic': 'niche-1'},
    )
    upsert_mock = MagicMock(
        side_effect=ValueError('month must be in 1..12'),
    )
    monkeypatch.setattr(cv_write_entities, 'upsert_education', upsert_mock)

    data = {'slug': 'smoke-edu', 'niches': ['generic'], 'priority': {}}
    with pytest.raises(ServiceError) as excinfo:
        content_service.upsert_entity(entity='education', data=data)

    assert excinfo.value.code == 1102
    assert excinfo.value.error_code == 'INVALID_FIELD_VALUE'
    assert excinfo.value.message == (
        'valor invalido en education: month must be in 1..12'
    )
