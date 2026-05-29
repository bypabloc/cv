"""AC-27: MfaMethodService.confirm del primer metodo revoca sesiones.

Given un user sin MFA (count antes=0) que confirma su primer metodo
  (count despues=1),
When se invoca confirm,
Then SessionService.revoke_all_for_user es llamado (transicion 0->1).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_mfa_method_service_confirm_first_revokes(monkeypatch):
    from services import mfa_method_service
    from shared.db.models import AuthMfaKind

    confirmed_method = MagicMock()
    # list_mfa_methods devuelve 1 metodo confirmado (despues del confirm).
    confirmed_method.confirmed_at = object()

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    # count_active: 0 antes, 1 despues.
    counts = iter([0, 1])
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
        lambda _s, *, user_id: [confirmed_method],
    )

    revoked = {}
    fake_session_svc = MagicMock()
    fake_session_svc.revoke_all_for_user.side_effect = lambda *, user_id: (
        revoked.update(user_id=user_id)
    )
    monkeypatch.setattr(
        mfa_method_service,
        'SessionService',
        lambda _c: fake_session_svc,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.confirm(user_id='user-1', kind=AuthMfaKind.TOTP)

    assert result is True
    assert revoked == {'user_id': 'user-1'}
