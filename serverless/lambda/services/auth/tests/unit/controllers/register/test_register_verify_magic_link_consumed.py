"""AC-16: link ya consumido -> 400 LINK_CONSUMED.

Given un token cuyo row tiene consumed_at != None,
When se invoca register.verify-magic-link,
Then devuelve is_valid=False, code 4006, status 400.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_with_token, _make_magic_link


def test_register_verify_magic_link_consumed(monkeypatch):
    """AC-16: link consumido -> 400 LINK_CONSUMED."""
    from controllers.register import verify_magic_link

    consumed_link = _make_magic_link(consumed=True)

    link_svc = MagicMock()
    link_svc.verify.return_value = None
    link_svc.get_state.return_value = consumed_link

    monkeypatch.setattr(
        verify_magic_link, 'MagicLinkService', lambda _c: link_svc,
    )
    monkeypatch.setattr(verify_magic_link, 'UserService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_magic_link, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_magic_link, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        verify_magic_link, 'RateLimitService', lambda _c: MagicMock(),
    )

    event = _make_event_with_token(token='C' * 32)
    controller = verify_magic_link.VerifyMagicLink(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4006
    assert result['status'] == 400
    assert result['data']['error'] == 'LINK_CONSUMED'
