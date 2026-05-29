"""setup-email-code con user autenticado -> 204 y activa el metodo.

Given un user activo,
When se invoca mfa.setup-email-code,
Then activa el metodo email_code y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_setup_email_code_ok(monkeypatch):
    """email-code activado -> 204."""
    from controllers.mfa import setup_email_code

    user = _make_user(status='active')

    mfa_svc = MagicMock()

    monkeypatch.setattr(
        setup_email_code,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        setup_email_code,
        'MfaMethodService',
        lambda _c: mfa_svc,
    )
    monkeypatch.setattr(
        setup_email_code,
        'AuditService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        setup_email_code,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event()
    result = setup_email_code.SetupEmailCode(event=event).run()

    assert result['is_valid'] is True
    assert result['status'] == 204
    mfa_svc.setup_email_code.assert_called_once_with(user_id=user.id)
