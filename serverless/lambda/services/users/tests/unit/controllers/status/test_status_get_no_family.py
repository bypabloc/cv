"""status.get con un access JWT legacy (sin family_id) -> current_session_id None.

Given un user activo cuyo access JWT NO lleva family_id (token legacy),
When se invoca status.get,
Then current_session_id es None (no rompe) y user_id se devuelve igual.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_status_get_no_family_id(monkeypatch):
    """family_id None -> current_session_id None."""
    from controllers.status import get as ctl

    user = _make_user(
        user_id='0193b8a0-0000-7000-8000-000000000008',
        status='active',
        failed_attempts=0,
    )

    profile_svc = MagicMock()
    profile_svc.mfa_summary.return_value = {
        'mfa_configured': False,
        'mfa_methods': [],
        'webauthn_count': 0,
        'recovery_codes_remaining': 0,
    }

    claims = MagicMock(family_id=None)
    monkeypatch.setattr(
        ctl, 'authenticate', lambda *_a, **_k: (user, claims),
    )
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event()
    result = ctl.Get(event=event).run()

    assert result['is_valid'] is True
    assert result['data']['user_id'] == str(user.id)
    assert result['data']['current_session_id'] is None
