"""reorder de un niche inexistente -> 4404 NICHE_NOT_FOUND.

Given un slug de niche que no existe en tax_niches,
When se invoca reorder,
Then ServiceError 4404 NICHE_NOT_FOUND y nada se reescribe.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest


@contextmanager
def _ctx(session):
    yield session


def test_reorder_niche_not_found(monkeypatch):
    from services import reorder_service
    from services._errors import ServiceError

    fake_session = MagicMock()
    niche_result = MagicMock()
    niche_result.scalar_one_or_none.return_value = None
    fake_session.execute.return_value = niche_result
    monkeypatch.setattr(
        reorder_service, 'db_session', lambda: _ctx(fake_session),
    )
    reorder_mock = MagicMock()
    monkeypatch.setattr(
        reorder_service, 'reorder_niche_priorities', reorder_mock,
    )

    with pytest.raises(ServiceError) as exc:
        reorder_service.reorder(
            entity_type='project',
            niche='no-existe',
            ordered_slugs=['a'],
        )

    assert exc.value.code == 4404
    assert exc.value.error_code == 'NICHE_NOT_FOUND'
    reorder_mock.assert_not_called()
