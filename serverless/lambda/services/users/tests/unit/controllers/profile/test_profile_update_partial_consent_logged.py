"""AC-2/AC-3: update parcial con marketing_consent cambiado -> consent log.

Given un user con marketing_consent=False,
When se invoca profile.update con marketing_consent=True,
Then actualiza el perfil y ConsentService.log es llamado (GDPR).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_profile_update_partial_consent_logged(monkeypatch):
    """AC-2/AC-3: marketing_consent cambia -> ConsentService.log llamado."""
    from controllers.profile import update as ctl

    user = _make_user(marketing_consent=False)

    updated = _make_user(
        user_id=user.id,
        email=user.email,
        display_name='New Name',
        locale='es',
        timezone='America/Santiago',
        marketing_consent=True,
    )

    profile_svc = MagicMock()
    profile_svc.update.return_value = updated
    consent_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'ConsentService', lambda _c: consent_svc)
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'marketing_consent': True})
    result = ctl.Update(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['marketing_consent'] is True
    consent_svc.log.assert_called_once_with(
        user_id=user.id,
        field='marketing_consent',
        old_value='False',
        new_value='True',
        ip='203.0.113.10',
        user_agent='pytest',
    )
