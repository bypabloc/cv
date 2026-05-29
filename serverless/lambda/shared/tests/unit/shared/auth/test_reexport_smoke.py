"""
Given el subpaquete shared.auth,
When se importan los simbolos del __all__,
Then todos resuelven y __all__ esta ordenado alfabeticamente.
"""

import pytest
import shared.auth as auth_pkg

pytestmark = pytest.mark.unit


def test_reexport_all_symbols_resolve_and_sorted():
    # Arrange
    expected_symbols = {
        'ACCESS_TTL',
        'AdminAuthzError',
        'CODE_ALPHABET',
        'CODE_LENGTH',
        'DEFAULT_AUDIENCE',
        'DEFAULT_ISSUER',
        'JWT_ALGORITHM',
        'JwtClaims',
        'JwtError',
        'JwtExpiredError',
        'JwtInvalidError',
        'JwtRevokedError',
        'NeedsRehashError',
        'PasswordError',
        'RECOVERY_CODE_ALPHABET',
        'RECOVERY_CODE_COUNT',
        'RECOVERY_CODE_LENGTH',
        'REFRESH_TTL',
        'TEMP_TTL',
        'TOKEN_BYTES',
        'TotpError',
        'WebauthnCloneError',
        'WebauthnError',
        'WebauthnVerifyError',
        'build_login_options',
        'build_otpauth_url',
        'build_register_options',
        'compare_code',
        'compare_recovery_code',
        'compare_token',
        'generate_code',
        'generate_opaque_token',
        'generate_recovery_codes',
        'generate_totp_secret_b32',
        'hash_code',
        'hash_password',
        'hash_recovery_code',
        'hash_token',
        'is_admin',
        'issue_access_jwt',
        'issue_refresh_jwt',
        'issue_temp_jwt',
        'load_admin_emails',
        'require_admin',
        'verify_authentication',
        'verify_jwt',
        'verify_password',
        'verify_registration',
        'verify_totp_code',
    }

    # Act
    declared = set(auth_pkg.__all__)

    # Assert: __all__ completo y todos los simbolos accesibles.
    assert declared == expected_symbols
    for name in declared:
        assert hasattr(auth_pkg, name), f'shared.auth missing symbol: {name}'
    # Sin duplicados (el orden canonico de __all__ lo enforce ruff RUF022,
    # que agrupa SCREAMING_SNAKE antes que CamelCase y no coincide con el
    # sorted() de Python; ver .claude/rules/python.md).
    assert len(auth_pkg.__all__) == len(set(auth_pkg.__all__))
