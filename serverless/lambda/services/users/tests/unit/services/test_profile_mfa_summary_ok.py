"""ProfileService.mfa_summary — agrega el estado MFA del user.

Given un user con 1 metodo TOTP confirmado, 1 webauthn activo y 4 recovery
codes restantes,
When se invoca mfa_summary,
Then devuelve mfa_configured True, los kinds confirmados, el count webauthn
y los recovery codes restantes.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_mfa_summary_ok(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    totp = SimpleNamespace(
        kind=SimpleNamespace(value='totp'),
        confirmed_at='2026-01-01',
        disabled_at=None,
    )
    webauthn = SimpleNamespace(disabled_at=None)

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        profile_service, 'count_active_mfa', lambda _s, *, user_id: 2,
    )
    monkeypatch.setattr(
        profile_service, 'list_mfa_methods', lambda _s, *, user_id: [totp],
    )
    monkeypatch.setattr(
        profile_service,
        'get_webauthn_credentials',
        lambda _s, *, user_id: [webauthn],
    )
    monkeypatch.setattr(
        profile_service,
        'count_remaining_recovery_codes',
        lambda _s, *, user_id: 4,
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.mfa_summary(user_id='user-1')

    assert result == {
        'mfa_configured': True,
        'mfa_methods': ['totp'],
        'webauthn_count': 1,
        'recovery_codes_remaining': 4,
    }
