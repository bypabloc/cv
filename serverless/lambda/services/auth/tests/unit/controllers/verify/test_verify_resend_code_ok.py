"""AC-19: temp_token valido + sin throttle -> re-emite code + magic-link.

Given un temp_token valido y la ultima emision hace > 60s,
When se invoca verify.resend-code,
Then invalida los previos, publica code + magic-link nuevos y rota el temp.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_resend_code, _make_jwt_claims, _make_user


def test_verify_resend_code_ok(monkeypatch):
    """AC-19: resend OK -> nuevo temp_token."""
    from controllers.verify import resend_code

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='register')
    user = _make_user(user_id=uid, status='pending')

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    code_svc = MagicMock()
    code_svc.seconds_until_resend_allowed.return_value = 0
    code_svc.generate_and_persist.return_value = ('ABCDEFGH', b'hash')

    link_svc = MagicMock()
    link_svc.generate_and_persist.return_value = ('TOKEN', b'thash')

    email_svc = MagicMock()
    flow_svc = MagicMock()
    flow_svc.advance_step.return_value = ('NEW-TEMP-JWT', MagicMock())
    audit_svc = MagicMock()
    rl_svc = MagicMock()

    monkeypatch.setattr(resend_code, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(resend_code, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(resend_code, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(resend_code, 'MagicLinkService', lambda _c: link_svc)
    monkeypatch.setattr(
        resend_code,
        'EmailDispatchService',
        lambda _c: email_svc,
    )
    monkeypatch.setattr(resend_code, 'FlowService', lambda _c: flow_svc)
    monkeypatch.setattr(resend_code, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(resend_code, 'RateLimitService', lambda _c: rl_svc)

    event = _make_event_resend_code()
    controller = resend_code.ResendCode(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['temp_token'] == 'NEW-TEMP-JWT'
    assert result['data']['expires_in'] == 300
    user_svc.invalidate_active_codes_and_links.assert_called_once()
    # UN solo email unificado (magic-link + code); el kind sale del flow.
    assert email_svc.publish_unified.call_count == 1
    email_svc.publish_magic_link.assert_not_called()
    email_svc.publish_code.assert_not_called()
    assert email_svc.publish_unified.call_args.kwargs['kind'] == (
        'register-unified'
    )
