"""
Given un SSM SecureString cifrado con una KMS key,
When shared.aws.ssm.get_secret lo lee con decrypt,
Then devuelve el valor descifrado en claro.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_ssm_get_secret_kms_decrypt_e2e(ssm_with_kms: object) -> None:
    """get_secret descifra un SecureString KMS y devuelve el valor."""
    # Arrange
    from shared.aws.ssm import clear_cache, get_secret

    ssm_with_kms.client.put_parameter(
        Name='/portfolio/turnstile-secret',
        Value='super-secret-token',
        Type='SecureString',
        KeyId=ssm_with_kms.kms_key_id,
    )
    clear_cache()

    # Act
    secret = get_secret('/portfolio/turnstile-secret')

    # Assert
    assert secret == 'super-secret-token'
