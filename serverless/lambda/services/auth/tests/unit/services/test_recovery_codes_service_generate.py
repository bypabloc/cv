"""RecoveryCodesService.generate persiste hashes y devuelve los codes plain.

Given generate_recovery_codes/hash_recovery_code mockeados,
When se invoca generate,
Then regenerate_recovery_codes recibe los 10 hashes y devuelve los plain.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_recovery_codes_service_generate_persists_hashes(monkeypatch):
    from services import recovery_codes_service

    codes = [f'CODE{i:06d}' for i in range(10)]
    captured = {}

    monkeypatch.setattr(
        recovery_codes_service,
        'db_session',
        _fake_session,
    )
    monkeypatch.setattr(
        recovery_codes_service,
        'generate_recovery_codes',
        lambda: codes,
    )
    monkeypatch.setattr(
        recovery_codes_service,
        'hash_recovery_code',
        lambda code: f'hash:{code}',
    )

    def fake_regen(_s, *, user_id, code_hashes):
        captured['user_id'] = user_id
        captured['hashes'] = code_hashes

    monkeypatch.setattr(
        recovery_codes_service,
        'regenerate_recovery_codes',
        fake_regen,
    )

    svc = recovery_codes_service.RecoveryCodesService(app_config=object())
    result = svc.generate(user_id='user-1')

    assert result == codes
    assert captured['user_id'] == 'user-1'
    assert captured['hashes'] == [f'hash:{c}' for c in codes]
