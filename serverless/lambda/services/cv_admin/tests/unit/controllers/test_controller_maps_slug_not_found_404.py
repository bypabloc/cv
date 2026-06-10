"""Controller traduce ServiceError 4404 a {is_valid: False, status: 404}.

Given el service levanta ServiceError 4404 SLUG_NOT_FOUND,
When se ejecuta delete_experience.run(),
Then el resultado es {is_valid: False, code: 4404, status: 404} con el
error_code en data.
"""

from unittest.mock import MagicMock

import pytest

from ._helpers import _make_admin_user, _make_authed_event


@pytest.fixture(autouse=True)
def _guards(monkeypatch):
    from controllers import _base

    monkeypatch.setattr(
        _base, 'require_active_user', lambda *_a, **_k: _make_admin_user(),
    )
    monkeypatch.setattr(_base, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(_base, 'RateLimitService', lambda _c: MagicMock())


def test_controller_maps_slug_not_found_404(monkeypatch):
    from services import content_service
    from services._errors import ServiceError

    def _boom(**_kwargs):
        raise ServiceError(
            "experience con slug 'nope' no existe",
            code=4404,
            error_code='SLUG_NOT_FOUND',
            detail={'entity': 'experience', 'slug': 'nope'},
        )

    monkeypatch.setattr(content_service, 'delete_entity', _boom)

    from controllers.content import delete_experience as ctl

    event = _make_authed_event(data={'slug': 'nope'})
    result = ctl.DeleteExperience(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4404
    assert result['status'] == 404
    assert result['data']['error_code'] == 'SLUG_NOT_FOUND'
    assert result['data']['detail'] == {
        'entity': 'experience', 'slug': 'nope',
    }
