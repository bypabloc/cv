"""AC-7: security.password-set-required marca/desmarca el flag de la password.

Given un user autenticado con password,
When se invoca security.password-set-required {required},
Then actualiza auth_credentials.required y devuelve 204. 404 si no hay
password. El invariante ">=1 required" lo garantiza el fallback passwordless
(no hay 409): desmarcar la password siempre es seguro.
"""

from unittest.mock import MagicMock

import pytest

from .._helpers import _make_authed_event, _make_user


@pytest.mark.parametrize('required', [True, False])
def test_password_set_required_ok(monkeypatch, required):
    """AC-7: set-required (true/false) -> 204."""
    from controllers.security import password_set_required

    user = _make_user(status='active')
    password_svc = MagicMock()
    password_svc.set_required.return_value = True

    monkeypatch.setattr(
        password_set_required, 'require_active_user', lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        password_set_required, 'PasswordService', lambda _c: password_svc,
    )
    monkeypatch.setattr(
        password_set_required, 'AuditService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        password_set_required, 'RateLimitService', lambda _c: MagicMock(),
    )

    event = _make_authed_event(data={'required': required})
    result = password_set_required.PasswordSetRequired(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    password_svc.set_required.assert_called_once_with(
        user_id=user.id, required=required,
    )


def test_password_set_required_no_password_404(monkeypatch):
    """AC-7: el user no tiene password -> 404 NOT_FOUND."""
    from controllers.security import password_set_required

    user = _make_user(status='active')
    password_svc = MagicMock()
    password_svc.set_required.return_value = False

    monkeypatch.setattr(
        password_set_required, 'require_active_user', lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        password_set_required, 'PasswordService', lambda _c: password_svc,
    )
    monkeypatch.setattr(
        password_set_required, 'AuditService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        password_set_required, 'RateLimitService', lambda _c: MagicMock(),
    )

    event = _make_authed_event(data={'required': False})
    result = password_set_required.PasswordSetRequired(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
