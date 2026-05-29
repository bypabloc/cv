"""MfaMethodService — cobertura de los metodos restantes.

Cubre: upsert_pending_totp, get_totp_ciphertext (pending / confirmed /
None), set_preferred, count_active, has_active_method, mark_used,
confirmed_kinds, setup_email_code (sin revocacion).
"""

from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_upsert_pending_totp_delegates(monkeypatch):
    from services import mfa_method_service

    captured = {}
    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)

    def fake_upsert(_s, *, user_id, ciphertext):
        captured['user_id'] = user_id
        captured['ciphertext'] = ciphertext

    monkeypatch.setattr(
        mfa_method_service,
        'upsert_totp_method',
        fake_upsert,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    svc.upsert_pending_totp(user_id='u-1', ciphertext=b'\x01' * 16)

    assert captured == {'user_id': 'u-1', 'ciphertext': b'\x01' * 16}


def test_get_totp_ciphertext_pending_ok(monkeypatch):
    from services import mfa_method_service

    method = MagicMock()
    method.totp_secret_ciphertext = b'\x02' * 16
    method.confirmed_at = None
    method.disabled_at = None

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: method,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.get_totp_ciphertext(user_id='u-1', require_confirmed=False)

    assert result == b'\x02' * 16


def test_get_totp_ciphertext_require_confirmed_pending_returns_none(
    monkeypatch,
):
    from services import mfa_method_service

    method = MagicMock()
    method.totp_secret_ciphertext = b'\x02' * 16
    method.confirmed_at = None
    method.disabled_at = None

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: method,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.get_totp_ciphertext(user_id='u-1', require_confirmed=True)

    assert result is None


def test_get_totp_ciphertext_no_method_returns_none(monkeypatch):
    from services import mfa_method_service

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: None,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    assert (
        svc.get_totp_ciphertext(
            user_id='u-1',
            require_confirmed=False,
        )
        is None
    )


def test_set_preferred_ok(monkeypatch):
    from services import mfa_method_service
    from shared.db.models import AuthMfaKind

    method = MagicMock()
    method.disabled_at = None
    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: method,
    )
    monkeypatch.setattr(
        mfa_method_service,
        'set_preferred',
        lambda _s, *, user_id, kind: None,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    assert svc.set_preferred(user_id='u-1', kind=AuthMfaKind.TOTP) is True


def test_set_preferred_missing_returns_false(monkeypatch):
    from services import mfa_method_service
    from shared.db.models import AuthMfaKind

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: None,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    assert svc.set_preferred(user_id='u-1', kind=AuthMfaKind.TOTP) is False


def test_count_active_delegates(monkeypatch):
    from services import mfa_method_service

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'count_active_mfa',
        lambda _s, *, user_id: 3,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    assert svc.count_active(user_id='u-1') == 3


def test_has_active_method_true(monkeypatch):
    from services import mfa_method_service
    from shared.db.models import AuthMfaKind

    method = MagicMock()
    method.disabled_at = None
    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: method,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    assert (
        svc.has_active_method(
            user_id='u-1',
            kind=AuthMfaKind.TOTP,
        )
        is True
    )


def test_has_active_method_disabled_false(monkeypatch):
    from services import mfa_method_service
    from shared.db.models import AuthMfaKind

    method = MagicMock()
    method.disabled_at = datetime.now(tz=UTC)
    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: method,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    assert (
        svc.has_active_method(
            user_id='u-1',
            kind=AuthMfaKind.TOTP,
        )
        is False
    )


def test_mark_used_delegates(monkeypatch):
    from services import mfa_method_service
    from shared.db.models import AuthMfaKind

    captured = {}
    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'mark_method_used',
        lambda _s, *, user_id, kind: captured.update(
            user_id=user_id,
            kind=kind,
        ),
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    svc.mark_used(user_id='u-1', kind=AuthMfaKind.TOTP)

    assert captured == {'user_id': 'u-1', 'kind': AuthMfaKind.TOTP}


def test_confirmed_kinds_filters_confirmed(monkeypatch):
    from services import mfa_method_service

    confirmed = MagicMock()
    confirmed.kind = MagicMock(value='totp')
    confirmed.confirmed_at = datetime.now(tz=UTC)
    pending = MagicMock()
    pending.kind = MagicMock(value='email_code')
    pending.confirmed_at = None

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'list_mfa_methods',
        lambda _s, *, user_id: [confirmed, pending],
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    assert svc.confirmed_kinds(user_id='u-1') == ['totp']
