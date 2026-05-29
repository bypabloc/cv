"""TotpService.verify descifra el secret y verifica el code -> True.

Given un ciphertext que kms_decrypt mapea a un secret base32 conocido y
  el code TOTP actual de ese secret (pyotp source-of-truth),
When se invoca verify,
Then devuelve True.
"""

from unittest.mock import MagicMock

import pyotp


def test_totp_service_decrypt_and_verify_ok(monkeypatch):
    from services import totp_service

    secret_b32 = pyotp.random_base32()
    current_code = pyotp.TOTP(secret_b32).now()

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
        code=current_code,
    )

    assert result is True
