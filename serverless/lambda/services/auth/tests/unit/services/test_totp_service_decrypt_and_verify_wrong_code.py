"""TotpService.verify con code incorrecto -> False.

Given un secret conocido y un code que NO es el actual,
When se invoca verify,
Then devuelve False.
"""

from unittest.mock import MagicMock

import pyotp


def test_totp_service_decrypt_and_verify_wrong_code(monkeypatch):
    from services import totp_service

    secret_b32 = pyotp.random_base32()

    monkeypatch.setattr(
        totp_service,
        'kms_decrypt',
        lambda *, ciphertext, encryption_context: secret_b32.encode('utf-8'),
    )

    cfg = MagicMock(kms_totp_key_id='alias/portfolio-lambdas')
    svc = totp_service.TotpService(cfg)
    result = svc.verify(
        user_id='user-1',
        ciphertext=b'\x01' * 16,
        code='000000',
    )

    assert result is False
