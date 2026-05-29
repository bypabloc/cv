"""TotpService.encrypt_secret cifra con la CMK + EncryptionContext del user.

Given un secret_b32 y un user_id,
When se invoca encrypt_secret,
Then kms_encrypt es llamado con key_id de config + context {user_id, purpose}.
"""

from unittest.mock import MagicMock


def test_totp_service_encrypt_uses_context(monkeypatch):
    from services import totp_service

    captured = {}

    def fake_encrypt(*, plaintext, key_id, encryption_context):
        captured['plaintext'] = plaintext
        captured['key_id'] = key_id
        captured['context'] = encryption_context
        return b'\xaa' * 16

    monkeypatch.setattr(totp_service, 'kms_encrypt', fake_encrypt)

    cfg = MagicMock(kms_totp_key_id='alias/portfolio-lambdas')
    svc = totp_service.TotpService(cfg)
    result = svc.encrypt_secret(secret_b32='JBSWY3DPEHPK3PXP', user_id='u-1')

    assert result == b'\xaa' * 16
    assert captured['key_id'] == 'alias/portfolio-lambdas'
    assert captured['context'] == {'user_id': 'u-1', 'purpose': 'totp'}
    assert captured['plaintext'] == b'JBSWY3DPEHPK3PXP'
