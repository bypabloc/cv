"""AC-4: set-preferred con metodo existente -> 204.

Given un user con el metodo activo,
When se invoca mfa.set-preferred con kind=email_code,
Then marca el metodo como preferido y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_set_preferred_ok(monkeypatch):
    """AC-4: set-preferred OK -> 204."""
    from controllers.mfa import set_preferred
    from shared.db.models import AuthMfaKind

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.set_preferred.return_value = True

    monkeypatch.setattr(
        set_preferred,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(set_preferred, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(set_preferred, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        set_preferred,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(data={'kind': 'email_code'})
    result = set_preferred.SetPreferred(event=event).run()

    assert result['is_valid'] is True
    assert result['status'] == 204
    mfa_svc.set_preferred.assert_called_once_with(
        user_id=user.id,
        kind=AuthMfaKind.EMAIL_CODE,
    )
