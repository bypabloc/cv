"""AC-8: refresh VIGENTE de una familia ya revocada -> 401 (no rota).

Given un refresh JWT valido cuyo jti propio NO esta blacklisted, pero
  cuya familia ya fue revocada por un reuso previo (existe el centinela
  jti == family_id en la blacklist),
When se invoca session.refresh,
Then revoca (re-asegura) la familia y devuelve 401 TOKEN_REUSE_DETECTED,
  SIN emitir tokens nuevos.

Regresion: antes el controller solo miraba is_blacklisted(jti) propio,
asi el refresh aun vigente de una familia comprometida sobrevivia a la
revocacion — rompiendo la garantia de AC-8 ("revocar TODA la familia").
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_refresh, _make_session_claims


def test_session_refresh_family_revoked(monkeypatch):
    """AC-8: familia revocada (centinela) -> 401 aunque el jti no lo este."""
    from controllers.session import refresh

    uid = uuid4()
    fid = uuid4()
    claims = _make_session_claims(typ='refresh', user_id=uid, family_id=fid)

    jwt_svc = MagicMock()
    jwt_svc.verify_allow_revoked.return_value = claims
    # El jti propio NO esta blacklisted; el centinela de la familia SI
    # (jti == family_id, escrito por revoke_family en el reuso previo).
    jwt_svc.is_blacklisted.side_effect = lambda *, jti: str(jti) == str(fid)

    monkeypatch.setattr(refresh, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(refresh, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(refresh, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_refresh()
    result = refresh.Refresh(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4004
    assert result['status'] == 401
    assert result['data']['error'] == 'TOKEN_REUSE_DETECTED'
    jwt_svc.revoke_family.assert_called_once_with(
        family_id=fid, user_id=uid, exp=claims.exp,
    )
    jwt_svc.issue_access.assert_not_called()
    jwt_svc.issue_refresh.assert_not_called()
