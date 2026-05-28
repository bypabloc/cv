"""FlowService — patron rolling temp JWT (verify + advance + terminate)."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

_TEST_JWT_KEY = 'X' * 40


def _stub_app_config():
    return SimpleNamespace(
        jwt_secret=_TEST_JWT_KEY,
        jwt_issuer='portfolio-auth',
        jwt_audience='portfolio',
        jwt_blacklist_table_name='portfolio-jwt-blacklist-test',
    )


def test_advance_step_blacklists_old_jti_and_returns_new_temp(monkeypatch):
    from services import flow_service, jwt_service
    from shared.auth import issue_temp_jwt

    monkeypatch.setattr(
        jwt_service.BlacklistService,
        'is_blacklisted',
        lambda _self, *, jti: False,
    )
    fake_put = MagicMock()
    monkeypatch.setattr(jwt_service.BlacklistService, 'put', fake_put)

    svc = flow_service.FlowService(_stub_app_config())
    user_id = uuid4()

    # Construir un temp con step=1 que el service rotara a step=2.
    _, claims_step1 = issue_temp_jwt(
        user_id=user_id,
        flow='register',
        step=1,
        secret=_TEST_JWT_KEY,
    )

    new_token, new_claims = svc.advance_step(claims_step1)

    fake_put.assert_called_once()
    assert new_claims.step == 2
    assert new_claims.flow == 'register'
    assert new_token != ''


def test_terminate_flow_returns_access_refresh_and_family(monkeypatch):
    from services import flow_service, jwt_service
    from shared.auth import issue_temp_jwt

    monkeypatch.setattr(
        jwt_service.BlacklistService,
        'is_blacklisted',
        lambda _self, *, jti: False,
    )
    monkeypatch.setattr(jwt_service.BlacklistService, 'put', MagicMock())

    svc = flow_service.FlowService(_stub_app_config())
    user_id = uuid4()

    _, claims = issue_temp_jwt(
        user_id=user_id, flow='register', step=2, secret=_TEST_JWT_KEY,
    )

    access_str, refresh_str, family_id = svc.terminate_flow(
        user_id=user_id, claims=claims,
    )

    assert access_str
    assert refresh_str
    assert family_id is not None
