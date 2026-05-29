"""MfaMethodService.setup_email_code: inserta el metodo (no primer MFA = no revoke).

Given un user que ya tiene un metodo MFA (count antes=1, despues=2),
When se invoca setup_email_code (sin metodo email_code previo),
Then inserta el row y NO revoca sesiones (no es el primer MFA).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


def test_setup_email_code_not_first_no_revoke(monkeypatch):
    from services import mfa_method_service

    session = MagicMock()

    @contextmanager
    def _fake_session():
        yield session

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    # count_active: 1 antes, 2 despues (no transicion 0->1).
    counts = iter([1, 2])
    monkeypatch.setattr(
        mfa_method_service,
        'count_active_mfa',
        lambda _s, *, user_id: next(counts),
    )
    # No existe metodo email_code -> entra al branch del INSERT.
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: None,
    )

    fake_session_svc = MagicMock()
    monkeypatch.setattr(
        mfa_method_service,
        'SessionService',
        lambda _c: fake_session_svc,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.setup_email_code(user_id='u-1')

    assert result is True
    session.add.assert_called_once()
    fake_session_svc.revoke_all_for_user.assert_not_called()


def test_confirm_not_first_no_revoke(monkeypatch):
    from services import mfa_method_service
    from shared.db.models import AuthMfaKind

    @contextmanager
    def _fake_session():
        yield MagicMock()

    confirmed_a = MagicMock()
    confirmed_a.confirmed_at = object()
    confirmed_b = MagicMock()
    confirmed_b.confirmed_at = object()

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    # count_active: 1 antes, 2 despues (no transicion 0->1).
    counts = iter([1, 2])
    monkeypatch.setattr(
        mfa_method_service,
        'count_active_mfa',
        lambda _s, *, user_id: next(counts),
    )
    monkeypatch.setattr(
        mfa_method_service,
        'confirm_mfa',
        lambda _s, *, user_id, kind: MagicMock(),
    )
    monkeypatch.setattr(
        mfa_method_service,
        'list_mfa_methods',
        lambda _s, *, user_id: [confirmed_a, confirmed_b],
    )

    fake_session_svc = MagicMock()
    monkeypatch.setattr(
        mfa_method_service,
        'SessionService',
        lambda _c: fake_session_svc,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.confirm(user_id='u-1', kind=AuthMfaKind.EMAIL_CODE)

    assert result is True
    fake_session_svc.revoke_all_for_user.assert_not_called()


def test_confirm_method_not_found_returns_false(monkeypatch):
    from services import mfa_method_service
    from shared.db.models import AuthMfaKind

    @contextmanager
    def _fake_session():
        yield MagicMock()

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'count_active_mfa',
        lambda _s, *, user_id: 0,
    )
    monkeypatch.setattr(
        mfa_method_service,
        'confirm_mfa',
        lambda _s, *, user_id, kind: None,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    assert svc.confirm(user_id='u-1', kind=AuthMfaKind.TOTP) is False
