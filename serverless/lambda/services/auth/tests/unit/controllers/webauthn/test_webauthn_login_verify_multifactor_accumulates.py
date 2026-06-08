"""login-verify acumula los factores previos del checklist via el temp_token.

Given un user con `required=[password, webauthn]` y un challenge de login
    valido, mas un temp_token step=2 cuyo flow ya lleva `password` satisfecho
    (`login-mfa:password`),
When se invoca webauthn.login-verify con ese temp_token,
Then acumula `satisfied=[password, webauthn]`, cubre los required y emite
    access+refresh (mfa_complete) + blacklistea el temp recibido (rolling).

Regresion guard del bug del checklist multi-factor: antes login-verify
hardcodeaba `satisfied=['webauthn']` y descartaba la password ya hecha, asi que
`decide_mfa_step` veia un required pendiente y nunca emitia tokens.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_temp_event


def test_webauthn_login_verify_accumulates_password_from_temp(monkeypatch):
    """temp con password satisfecho + webauthn -> emite tokens (mfa_complete)."""
    from controllers.webauthn import login_verify

    uid = uuid4()
    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())
    # El temp del checklist: step=2, flow con 'password' ya satisfecho, sub=uid.
    claims = MagicMock()
    claims.flow = 'login-mfa:password'
    claims.step = 2
    claims.sub = str(uid)
    claims.jti = 'TEMP-JTI'
    claims.exp = 9_999_999_999
    jwt_svc.verify.return_value = claims

    webauthn_svc = MagicMock()
    webauthn_svc.verify_login.return_value = b'\x10' * 16
    mfa_svc = MagicMock()
    mfa_svc.required_methods.return_value = ['password', 'webauthn']
    challenge_svc = MagicMock()
    challenge_svc.get_and_consume.return_value = {
        'user_id': str(uid),
        'kind': 'login',
        'state': {'s': 1},
    }

    monkeypatch.setattr(login_verify, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(login_verify, 'WebauthnService', lambda _c: webauthn_svc)
    monkeypatch.setattr(login_verify, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(
        login_verify, 'ChallengeService', lambda _c: challenge_svc,
    )
    monkeypatch.setattr(login_verify, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(login_verify, 'RateLimitService', lambda _c: MagicMock())
    from controllers.login import _mfa_login

    monkeypatch.setattr(
        _mfa_login, 'SessionTrackingService', lambda _c: MagicMock(),
    )

    event = _make_temp_event(
        data={
            'challenge_id': '01900000-0000-7000-8000-000000000001',
            'response': {'id': 'x'},
            'temp_token': 'TEMP-FROM-CHECKLIST',
        },
    )
    result = login_verify.LoginVerify(event=event).run()

    # Emite tokens (los 2 required cubiertos) — mfa_complete.
    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    assert result['data']['mfa_complete'] is True
    # El temp recibido se blacklistea (rolling).
    jwt_svc.blacklist.assert_called_once()
    assert jwt_svc.blacklist.call_args.kwargs['jti'] == 'TEMP-JTI'


def test_webauthn_login_verify_temp_other_user_degrades_to_webauthn_only(
    monkeypatch,
):
    """temp con sub de OTRO user -> NO acumula (anti cross-account): solo webauthn.

    El user del challenge tiene `required=[webauthn]` (passkey unico factor): con
    `satisfied=['webauthn']` cubre el required y emite tokens; el factor del temp
    ajeno se ignora y el temp NO se blacklistea.
    """
    from controllers.webauthn import login_verify

    uid = uuid4()
    other = uuid4()
    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())
    claims = MagicMock()
    claims.flow = 'login-mfa:password'
    claims.step = 2
    claims.sub = str(other)  # sub de otro user
    claims.jti = 'TEMP-JTI'
    claims.exp = 9_999_999_999
    jwt_svc.verify.return_value = claims

    webauthn_svc = MagicMock()
    webauthn_svc.verify_login.return_value = b'\x10' * 16
    mfa_svc = MagicMock()
    mfa_svc.required_methods.return_value = ['webauthn']
    challenge_svc = MagicMock()
    challenge_svc.get_and_consume.return_value = {
        'user_id': str(uid),
        'kind': 'login',
        'state': {'s': 1},
    }

    monkeypatch.setattr(login_verify, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(login_verify, 'WebauthnService', lambda _c: webauthn_svc)
    monkeypatch.setattr(login_verify, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(
        login_verify, 'ChallengeService', lambda _c: challenge_svc,
    )
    monkeypatch.setattr(login_verify, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(login_verify, 'RateLimitService', lambda _c: MagicMock())
    from controllers.login import _mfa_login

    monkeypatch.setattr(
        _mfa_login, 'SessionTrackingService', lambda _c: MagicMock(),
    )

    event = _make_temp_event(
        data={
            'challenge_id': '01900000-0000-7000-8000-000000000001',
            'response': {'id': 'x'},
            'temp_token': 'TEMP-FROM-OTHER-USER',
        },
    )
    result = login_verify.LoginVerify(event=event).run()

    # Emite tokens (webauthn cubre el unico required); el temp ajeno NO rota.
    assert result['is_valid'] is True
    assert result['data']['access_token'] == 'ACCESS-JWT'
    jwt_svc.blacklist.assert_not_called()
