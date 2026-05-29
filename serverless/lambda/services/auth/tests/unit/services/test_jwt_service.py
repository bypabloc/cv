"""JwtService — happy + sad path (issue/verify + blacklist hooks)."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

# JWT HS256 needs a string of reasonable entropy. Use a deterministic
# random-looking 40-char placeholder (NOT a real value).
_TEST_JWT_KEY = 'X' * 40


def _stub_app_config():
    """AppConfig stub que NO toca SSM (los valores son strings directos)."""
    return SimpleNamespace(
        jwt_secret=_TEST_JWT_KEY,
        jwt_issuer='portfolio-auth',
        jwt_audience='portfolio',
        jwt_blacklist_table_name='portfolio-jwt-blacklist-test',
    )


def test_issue_temp_and_verify_roundtrip(monkeypatch):
    """Emite un temp + verify_jwt lo decodifica con el mismo secret."""
    from services import jwt_service

    monkeypatch.setattr(
        jwt_service.BlacklistService,
        'is_blacklisted',
        lambda _self, *, jti: False,
    )

    svc = jwt_service.JwtService(_stub_app_config())
    user_id = uuid4()

    token_str, claims = svc.issue_temp(
        user_id=user_id,
        flow='register',
        step=1,
    )
    verified = svc.verify(token_str, expected_typ='temp')

    assert verified.sub == user_id
    assert verified.typ == 'temp'
    assert verified.flow == 'register'
    assert verified.step == 1


def test_verify_rejects_when_blacklisted(monkeypatch):
    """JwtService.verify levanta JwtRevokedError si el jti esta en DDB."""
    import pytest
    from services import jwt_service
    from shared.auth import JwtRevokedError

    monkeypatch.setattr(
        jwt_service.BlacklistService,
        'is_blacklisted',
        lambda _self, *, jti: True,
    )

    svc = jwt_service.JwtService(_stub_app_config())
    token_str, _ = svc.issue_access(user_id=uuid4())

    with pytest.raises(JwtRevokedError):
        svc.verify(token_str, expected_typ='access')


def test_verify_with_expected_flow_mismatch_raises(monkeypatch):
    """verify(expected_flow='login') sobre un temp emitido con flow='register' -> JwtInvalidError."""
    import pytest
    from services import jwt_service
    from shared.auth import JwtInvalidError

    monkeypatch.setattr(
        jwt_service.BlacklistService,
        'is_blacklisted',
        lambda _self, *, jti: False,
    )

    svc = jwt_service.JwtService(_stub_app_config())
    token_str, _ = svc.issue_temp(user_id=uuid4(), flow='register', step=1)

    with pytest.raises(JwtInvalidError):
        svc.verify(token_str, expected_typ='temp', expected_flow='login')


def test_issue_refresh_returns_token_with_family(monkeypatch):
    from services import jwt_service

    monkeypatch.setattr(
        jwt_service.BlacklistService,
        'is_blacklisted',
        lambda _self, *, jti: False,
    )

    svc = jwt_service.JwtService(_stub_app_config())
    user_id = uuid4()
    family_id = uuid4()

    token_str, claims = svc.issue_refresh(
        user_id=user_id,
        family_id=family_id,
    )

    assert claims.typ == 'refresh'
    assert claims.family_id == family_id
    assert token_str != ''


def test_revoke_family_delegates_to_blacklist_service(monkeypatch):
    from services import jwt_service

    fake = MagicMock()
    monkeypatch.setattr(jwt_service.BlacklistService, 'revoke_family', fake)

    svc = jwt_service.JwtService(_stub_app_config())
    svc.revoke_family(
        family_id='fam-1',
        user_id='user-x',
        exp=1_700_000_000,
    )

    fake.assert_called_once()


def test_blacklist_delegates_to_blacklist_service(monkeypatch):
    """jwt_service.blacklist() llama a BlacklistService.put."""
    from services import jwt_service

    fake_put = MagicMock()
    monkeypatch.setattr(jwt_service.BlacklistService, 'put', fake_put)

    svc = jwt_service.JwtService(_stub_app_config())
    svc.blacklist(
        jti='jti-1',
        exp=1_700_000_000,
        user_id='user-x',
        reason='logout',
    )

    fake_put.assert_called_once()
    kwargs = fake_put.call_args.kwargs
    assert kwargs['jti'] == 'jti-1'
    assert kwargs['reason'] == 'logout'
