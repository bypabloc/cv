"""
Given un user con un credential activo,
When se construyen las login options,
Then publicKey trae challenge + allowCredentials con el credential del user.
"""

from __future__ import annotations

from shared.auth import build_login_options


def test_webauthn_login_options() -> None:
    # Act
    options, state = build_login_options(
        rp_id='example.com',
        rp_name='Test',
        expected_origins=['https://example.com'],
        allowed_credentials=[b'cred-1'],
    )

    # Assert
    public_key = options['publicKey']
    assert isinstance(public_key['challenge'], str)
    assert len(public_key['allowCredentials']) == 1
    assert isinstance(state['challenge'], str)
