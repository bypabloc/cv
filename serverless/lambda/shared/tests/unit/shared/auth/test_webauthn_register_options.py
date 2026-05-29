"""
Given un user sin credentials previos,
When se construyen las register options,
Then el dict publicKey trae challenge + rp.id + user.id y el state es dict.
"""

from __future__ import annotations

from shared.auth import build_register_options


def test_webauthn_register_options() -> None:
    # Act
    options, state = build_register_options(
        rp_id='example.com',
        rp_name='Test',
        expected_origins=['https://example.com'],
        user_id=b'\x01' * 16,
        user_name='user@example.com',
        user_display_name='user@example.com',
        existing_credentials=[],
    )

    # Assert
    public_key = options['publicKey']
    assert isinstance(public_key['challenge'], str)
    assert public_key['rp']['id'] == 'example.com'
    assert isinstance(public_key['user']['id'], str)
    assert isinstance(state['challenge'], str)
