"""AC-13: login.send-email-code envia el code dentro del checklist.

Given un temp step=2 (`flow='login-mfa'`) valido,
When se invoca login.send-email-code,
Then genera+envia el email unificado (code + magic-link) y devuelve {ok:true}.
NO blacklistea el temp (el checklist sigue abierto).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_temp_event, _make_user


def test_login_send_email_code_ok(monkeypatch):
    """AC-13: send-email-code -> publica email unificado + ok:true."""
    from controllers.login import send_email_code

    uid = uuid4()
    user = _make_user(user_id=uid, status='active')

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = SimpleNamespace(
        sub=uid, jti='temp-jti', exp=9999999999, flow='login-mfa', step=2,
        typ='temp',
    )
    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user
    code_svc = MagicMock()
    code_svc.generate_and_persist.return_value = ('ABCDEFGH', MagicMock())
    link_svc = MagicMock()
    link_svc.generate_and_persist.return_value = ('TOKEN-XYZ', MagicMock())
    email_svc = MagicMock()

    monkeypatch.setattr(send_email_code, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(send_email_code, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(send_email_code, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(
        send_email_code, 'MagicLinkService', lambda _c: link_svc,
    )
    monkeypatch.setattr(
        send_email_code, 'EmailDispatchService', lambda _c: email_svc,
    )
    monkeypatch.setattr(send_email_code, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        send_email_code, 'RateLimitService', lambda _c: MagicMock(),
    )

    event = _make_temp_event(data={'temp_token': 'x' * 30})
    result = send_email_code.SendEmailCode(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == {'ok': True}
    email_svc.publish_unified.assert_called_once()
    assert (
        email_svc.publish_unified.call_args.kwargs['kind'] == 'login-unified'
    )
    # NO blacklistea el temp: el checklist sigue abierto.
    jwt_svc.blacklist.assert_not_called()
