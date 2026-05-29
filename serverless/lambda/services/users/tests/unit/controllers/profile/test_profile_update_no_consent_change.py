"""AC-3: update sin cambio de marketing_consent -> consent NO logueado.

Given un user con marketing_consent=False,
When se invoca profile.update con solo display_name (sin marketing_consent),
Then actualiza el perfil y ConsentService.log NO es llamado.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_profile_update_no_consent_change(monkeypatch):
    """AC-3: sin cambio de consent -> ConsentService.log no llamado."""
    from controllers.profile import update as ctl

    user = _make_user(marketing_consent=False)

    updated = _make_user(
        user_id=user.id,
        email=user.email,
        display_name='Renamed',
        locale=user.locale,
        timezone=user.timezone,
        marketing_consent=False,
    )

    profile_svc = MagicMock()
    profile_svc.update.return_value = updated
    consent_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'ConsentService', lambda _c: consent_svc)
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'display_name': 'Renamed'})
    result = ctl.Update(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['display_name'] == 'Renamed'
    assert consent_svc.log.call_count == 0
