"""
Given que se generan tokens opacos via secrets.token_urlsafe,
When se inspeccionan,
Then son url-safe (sin +, /, =) y length >= 32 chars.
"""

import pytest
from shared.auth import generate_opaque_token

pytestmark = pytest.mark.unit


def test_tokens_generate_is_url_safe_and_long_enough():
    # Arrange + Act
    value = generate_opaque_token()

    # Assert
    assert len(value) >= 32
    # url-safe b64: no +, /, =
    for forbidden in ('+', '/', '='):
        assert forbidden not in value
