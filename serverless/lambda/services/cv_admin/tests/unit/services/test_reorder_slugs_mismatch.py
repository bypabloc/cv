"""reorder exige ordered_slugs == conjunto exacto del niche.

Given el niche tiene {exp-a, exp-b} pero ordered_slugs trae
[exp-a, exp-zz],
When se invoca reorder,
Then ServiceError 1101 REORDER_SLUGS_MISMATCH con faltantes=['exp-b'] y
sobrantes=['exp-zz'], y nada se reescribe.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest


@contextmanager
def _ctx(session):
    yield session


def test_reorder_slugs_mismatch(monkeypatch):
    from services import reorder_service
    from services._errors import ServiceError

    fake_session = MagicMock()
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

    with pytest.raises(ServiceError) as exc:
        reorder_service.reorder(
            entity_type='experience',
            niche='generic',
            ordered_slugs=['exp-a', 'exp-zz'],
        )

    assert exc.value.code == 1101
    assert exc.value.error_code == 'REORDER_SLUGS_MISMATCH'
    assert exc.value.detail == {'missing': ['exp-b'], 'extra': ['exp-zz']}
    reorder_mock.assert_not_called()
