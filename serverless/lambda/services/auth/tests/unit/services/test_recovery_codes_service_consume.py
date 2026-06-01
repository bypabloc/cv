"""RecoveryCodesService.consume devuelve el resultado del repo.

Given consume_recovery_code devuelve True (code activo) o False (consumido),
When se invoca consume,
Then propaga el resultado.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_recovery_codes_service_consume_returns_true(monkeypatch):
    from services import recovery_codes_service

    monkeypatch.setattr(
        recovery_codes_service,
        'db_session',
        _fake_session,
    )
    monkeypatch.setattr(
        recovery_codes_service,
        'hash_recovery_code',
        lambda code: b'h',
    )
    monkeypatch.setattr(
        recovery_codes_service,
        'consume_recovery_code',
        lambda _s, *, user_id, code_hash: True,
    )

    svc = recovery_codes_service.RecoveryCodesService(app_config=object())
    assert svc.consume(user_id='user-1', code='ABCDEFGHJK') is True


def test_recovery_codes_service_consume_returns_false(monkeypatch):
    from services import recovery_codes_service

    monkeypatch.setattr(
        recovery_codes_service,
        'db_session',
        _fake_session,
    )
    monkeypatch.setattr(
        recovery_codes_service,
        'hash_recovery_code',
        lambda code: b'h',
    )
    monkeypatch.setattr(
        recovery_codes_service,
        'consume_recovery_code',
        lambda _s, *, user_id, code_hash: False,
    )

    svc = recovery_codes_service.RecoveryCodesService(app_config=object())
    assert svc.consume(user_id='user-1', code='ABCDEFGHJK') is False
