"""Controller traduce ServiceError 1101 a {is_valid: False, status: 400}.

Given el service levanta ServiceError 1101 REORDER_SLUGS_MISMATCH,
When se ejecuta reorder.run(),
Then el resultado es {is_valid: False, code: 1101, status: 400} con los
faltantes/sobrantes en data.detail.
"""

from unittest.mock import MagicMock

import pytest

from ._helpers import _make_admin_user, _make_authed_event


@pytest.fixture(autouse=True)
def _guards(monkeypatch):
    from controllers import _base
    from services import permission_checker

    monkeypatch.setattr(
        permission_checker,
        'require_active_user',
        lambda *_a, **_k: _make_admin_user(),
    )
    monkeypatch.setattr(_base, 'RateLimitService', lambda _c: MagicMock())


def test_controller_maps_reorder_mismatch_400(monkeypatch):
    from services import reorder_service
    from services._errors import ServiceError

    def _boom(**_kwargs):
        raise ServiceError(
            'mismatch',
            code=1101,
            error_code='REORDER_SLUGS_MISMATCH',
            detail={'missing': ['exp-b'], 'extra': ['exp-zz']},
        )

    monkeypatch.setattr(reorder_service, 'reorder', _boom)

    from controllers.content import reorder as ctl

    event = _make_authed_event(
        data={
            'entity_type': 'experience',
            'niche': 'generic',
            'ordered_slugs': ['exp-a', 'exp-zz'],
        },
    )
    result = ctl.Reorder(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 1101
    assert result['status'] == 400
    assert result['data']['detail'] == {
        'missing': ['exp-b'], 'extra': ['exp-zz'],
    }
