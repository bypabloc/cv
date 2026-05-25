"""
Given un SSM String plano (no cifrado),
When shared.aws.ssm.get_parameter lo lee,
Then devuelve el valor tal cual sin decrypt.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_ssm_get_parameter_string_e2e(ssm_with_kms: object) -> None:
    """get_parameter lee un String plano de SSM."""
    # Arrange
    from shared.aws.ssm import clear_cache, get_parameter

    ssm_with_kms.client.put_parameter(
        Name='/portfolio/owner-email',
        Value='owner@example.com',
        Type='String',
    )
    clear_cache()

    # Act
    value = get_parameter('/portfolio/owner-email')

    # Assert
    assert value == 'owner@example.com'
