"""AC-1: setup-totp con user autenticado -> 200 con secret_b32 + otpauth_url.

Given un user activo (access JWT valido) sin TOTP,
When se invoca mfa.setup-totp,
Then cifra y persiste el secret pendiente y devuelve secret_b32 + otpauth_url.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_setup_totp_ok(monkeypatch):
    """AC-1: 200 con secret_b32 + otpauth_url + persiste pending."""
    from controllers.mfa import setup_totp

    user = _make_user(email='visitor@example.com', status='active')

    totp_svc = MagicMock()
    totp_svc.generate_secret.return_value = 'JBSWY3DPEHPK3PXP'
    totp_svc.encrypt_secret.return_value = b'\x01' * 32
    totp_svc.otpauth_url.return_value = 'otpauth://totp/the-full-stack.com:x'
    mfa_svc = MagicMock()
    audit_svc = MagicMock()

    monkeypatch.setattr(
        setup_totp,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(setup_totp, 'TotpService', lambda _c: totp_svc)
    monkeypatch.setattr(setup_totp, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(setup_totp, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(setup_totp, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event()
    result = setup_totp.SetupTotp(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['secret_b32'] == 'JBSWY3DPEHPK3PXP'
    assert result['data']['otpauth_url'] == (
        'otpauth://totp/the-full-stack.com:x'
    )
    mfa_svc.upsert_pending_totp.assert_called_once_with(
        user_id=user.id,
        ciphertext=b'\x01' * 32,
    )
