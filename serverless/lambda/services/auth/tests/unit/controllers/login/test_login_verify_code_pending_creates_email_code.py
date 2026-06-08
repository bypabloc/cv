"""AC-1: login.verify-code del alta (pending) crea el email_code confirmado.

Given un user PENDING que verifica su code de alta (step=1, flow='login'),
When login.verify-code lo marca active,
Then ademas llama mfa_svc.ensure_email_code (el email queda verificado en el
  alta -> email_code configurado) y emite los tokens normalmente.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import (
    _make_event_with_code,
    _make_jwt_claims,
    _make_user,
)


def test_login_verify_code_pending_creates_email_code(monkeypatch):
    """El alta (pending->active) crea el email_code confirmado."""
    from controllers.login import _mfa_login, verify_code

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='login', step=1)
    user = _make_user(user_id=uid, status='pending')

    flow_svc = MagicMock()
    flow_svc.verify_temp_token.return_value = claims

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    code_svc = MagicMock()
    code_svc.verify.return_value = True

    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('ACC', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REF', MagicMock())

    mfa_svc = MagicMock()
    mfa_svc.required_methods.return_value = ['passwordless']

    monkeypatch.setattr(verify_code, 'FlowService', lambda _c: flow_svc)
    monkeypatch.setattr(verify_code, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(verify_code, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(verify_code, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_code, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(verify_code, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_code, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(
        _mfa_login, 'SessionTrackingService', lambda _c: MagicMock(),
    )

    event = _make_event_with_code(code='ABCDEFGH')
    result = verify_code.VerifyCode(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    user_svc.mark_active.assert_called_once_with(user)
    mfa_svc.ensure_email_code.assert_called_once_with(user_id=user.id)
