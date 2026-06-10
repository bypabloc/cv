"""El upsert pasa al service el payload en shape YAML (camelCase, sin meta).

Given un evento valido de upsert-experience con companyUrl + skills,
When se ejecuta UpsertExperience.run(),
Then content_service.upsert_entity recibe data con claves camelCase
(companyUrl, skillsTechnical) y SIN la clave _meta/meta.
"""

from unittest.mock import MagicMock

from ._helpers import (
    _experience_payload,
    _make_admin_user,
    _make_authed_event,
)


def test_upsert_experience_controller_payload_shape(monkeypatch):
    from controllers import _base
    from services import content_service

    monkeypatch.setattr(
        _base, 'require_active_user', lambda *_a, **_k: _make_admin_user(),
    )
    monkeypatch.setattr(_base, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(_base, 'RateLimitService', lambda _c: MagicMock())
    service_mock = MagicMock(
        return_value={'entity': 'smoke-exp', 'id': 'id-1'},
    )
    monkeypatch.setattr(content_service, 'upsert_entity', service_mock)

    from controllers.content import upsert_experience as ctl

    payload = _experience_payload()
    payload['companyUrl'] = 'https://smoke.example.com'
    payload['skillsTechnical'] = ['Python']
    event = _make_authed_event(data=payload)

    result = ctl.UpsertExperience(event=event).run()

    assert result['is_valid'] is True
    sent = service_mock.call_args.kwargs['data']
    assert sent['companyUrl'] == 'https://smoke.example.com'
    assert sent['skillsTechnical'] == ['Python']
    assert sent['slug'] == 'smoke-exp'
    assert '_meta' not in sent
    assert 'meta' not in sent
