"""AC-3: check-email de un user disabled/locked -> {exists, unavailable}.

Given un email que existe pero esta disabled o locked,
When se invoca login.check-email,
Then devuelve {exists:true, unavailable:true} SIN temp_token (no hay flujo
que continuar; anti-enumeration: mismo body para disabled/locked/deleted).
"""

import pytest

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


@pytest.mark.parametrize('status', ['disabled', 'locked', 'deleted'])
def test_check_email_unavailable(monkeypatch, status):
    """AC-3: disabled/locked/deleted -> unavailable, sin temp_token."""
    from controllers.login import check_email
    from shared.db.models.auth.enums import AuthUserStatus

    user = MagicMock()
    user.id = 'usr-unavail-1'
    user.status = AuthUserStatus(status)
    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    jwt_svc = MagicMock()

    monkeypatch.setattr(check_email, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        check_email, 'PasswordService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(check_email, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(check_email, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(check_email, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(
        check_email, 'verify_captcha_or_bypass', lambda *_a, **_k: {},
    )

    event = _make_event_register_start(email='blocked@example.com')
    result = check_email.CheckEmail(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == {'exists': True, 'unavailable': True}
    assert 'temp_token' not in result['data']
    # disabled/locked/deleted: NO se emite precheck.
    jwt_svc.issue_temp.assert_not_called()
