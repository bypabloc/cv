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
        'REFRESH_TTL',
        'TEMP_TTL',
        'TOKEN_BYTES',
        'compare_code',
        'compare_token',
        'generate_code',
        'generate_opaque_token',
        'hash_code',
        'hash_password',
        'hash_token',
        'issue_access_jwt',
        'issue_refresh_jwt',
        'issue_temp_jwt',
        'verify_jwt',
        'verify_password',
    }

    # Act
    declared = set(auth_pkg.__all__)

    # Assert: __all__ completo y todos los simbolos accesibles.
    assert declared == expected_symbols
    for name in declared:
        assert hasattr(auth_pkg, name), f'shared.auth missing symbol: {name}'
    # Ordenado alfabeticamente (case-sensitive matches sort default).
    assert list(auth_pkg.__all__) == sorted(auth_pkg.__all__)
