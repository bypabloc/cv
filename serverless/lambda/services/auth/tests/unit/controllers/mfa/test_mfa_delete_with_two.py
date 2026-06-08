"""delete de un metodo CONFIRMADO con total_mfa >= 2 -> 204 (hard-delete).

Given un user con el metodo confirmado + activo y total_mfa == 2,
When se invoca mfa.delete con uno,
Then borra el metodo (hard-delete) y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_delete_with_two(monkeypatch):
    """total_mfa == 2 + confirmado -> 204 + delete."""
    from controllers.mfa import delete
    from shared.db.models.auth.enums import AuthMfaKind

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.has_active_method.return_value = True
    mfa_svc.is_confirmed.return_value = True
    mfa_svc.count_active.return_value = 2

    monkeypatch.setattr(
        delete,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(delete, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(delete, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(delete, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'kind': 'email_code'})
    result = delete.Delete(event=event).run()

    assert result['is_valid'] is True
    assert result['status'] == 204
    mfa_svc.delete.assert_called_once_with(
        user_id=user.id,
        kind=AuthMfaKind.EMAIL_CODE,
    )
