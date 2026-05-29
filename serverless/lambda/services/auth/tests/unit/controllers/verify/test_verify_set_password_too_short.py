"""AC-4: password < 12 chars -> ValidationError (400) sin tocar negocio.

Given una password de menos de 12 chars,
When se invoca verify.set-password,
Then el modelo Pydantic la rechaza y el controller devuelve is_valid=False
     antes de hashear o persistir nada.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_set_password


def test_verify_set_password_too_short(monkeypatch):
    """Password corta -> validacion falla, no se persiste."""
    from controllers.verify import set_password

    user_svc = MagicMock()
    monkeypatch.setattr(set_password, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        set_password, 'RateLimitService', lambda _c: MagicMock()
    )

    # 11 chars (< 12 min).
    event = _make_event_set_password(password='short-pass1')
    controller = set_password.SetPassword(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    # ErrorCode.VALIDATION_ERROR — no llega al negocio.
    assert result['code'] == 1000
    user_svc.set_password_hash.assert_not_called()
