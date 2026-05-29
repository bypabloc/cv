"""
Given un secret base32 y un email,
When se construye el otpauth_url,
Then matchea otpauth://totp/ con issuer + email en el label y query.
"""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

from shared.auth.totp import build_otpauth_url


def test_totp_otpauth_url_format() -> None:
    # Act
    url = build_otpauth_url(
        secret_b32='JBSWY3DPEHPK3PXP',
        account_email='user@example.com',
        issuer='the-full-stack.com',
    )

    # Assert
    assert url.startswith('otpauth://totp/')
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert query['issuer'] == ['the-full-stack.com']
    # El path viene URL-encoded (@ -> %40); se compara descodificado.
    assert 'user@example.com' in unquote(parsed.path)
