"""TotpService.generate_secret + otpauth_url delegan a shared.auth.

Given los wrappers de shared.auth mockeados,
When se invoca generate_secret / otpauth_url,
Then devuelven el valor del wrapper con los argumentos esperados.
"""

from unittest.mock import MagicMock


def test_totp_service_generate_secret(monkeypatch):
    from services import totp_service

    monkeypatch.setattr(
        totp_service,
        'generate_totp_secret_b32',
        lambda: 'JBSWY3DPEHPK3PXP',
    )

    svc = totp_service.TotpService(MagicMock())
    assert svc.generate_secret() == 'JBSWY3DPEHPK3PXP'


def test_totp_service_otpauth_url(monkeypatch):
    from services import totp_service

    captured = {}

    def fake_build(*, secret_b32, account_email, issuer):
        captured['secret'] = secret_b32
        captured['email'] = account_email
        captured['issuer'] = issuer
        return 'otpauth://totp/the-full-stack.com:x@example.com'

    monkeypatch.setattr(totp_service, 'build_otpauth_url', fake_build)

    svc = totp_service.TotpService(MagicMock())
    url = svc.otpauth_url(secret_b32='SEC', email='x@example.com')

    assert url == 'otpauth://totp/the-full-stack.com:x@example.com'
    assert captured['issuer'] == 'the-full-stack.com'
    assert captured['email'] == 'x@example.com'
