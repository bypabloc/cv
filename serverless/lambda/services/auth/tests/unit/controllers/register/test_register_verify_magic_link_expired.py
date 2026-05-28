"""AC-17: link expirado o inexistente -> 400 LINK_EXPIRED.

Given un token sin row activo (no existe o expires_at < now),
When se invoca register.verify-magic-link,
Then devuelve is_valid=False, code 4007, status 400.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_with_token


def test_register_verify_magic_link_expired(monkeypatch):
    """AC-17: link expirado/inexistente -> 400 LINK_EXPIRED."""
    from controllers.register import verify_magic_link

    link_svc = MagicMock()
    link_svc.verify.return_value = None
    link_svc.get_state.return_value = None  # no existe

    monkeypatch.setattr(
        verify_magic_link, 'MagicLinkService', lambda _c: link_svc,
    )
    monkeypatch.setattr(verify_magic_link, 'UserService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_magic_link, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_magic_link, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        verify_magic_link, 'RateLimitService', lambda _c: MagicMock(),
    )

    event = _make_event_with_token(token='D' * 32)
    controller = verify_magic_link.VerifyMagicLink(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4007
    assert result['status'] == 400
    assert result['data']['error'] == 'LINK_EXPIRED'
