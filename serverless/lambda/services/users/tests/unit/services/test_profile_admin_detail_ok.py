"""ProfileService.admin_detail — user existente.

Given un user existente con MFA, sesiones y audit,
When se invoca admin_detail,
Then devuelve profile + mfa + sessions_count + recent_audit, sin exponer
password_hash ni TOTP secret.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_admin_detail_ok(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    user = SimpleNamespace(
        id='user-1',
        email='u@example.com',
        display_name='Neo',
        locale='es',
        timezone='UTC',
        marketing_consent=False,
        status=SimpleNamespace(value='active'),
        created_at=SimpleNamespace(isoformat=lambda: '2026-01-01T00:00:00'),
        deleted_at=None,
        email_verified_at=None,
        failed_attempts=0,
        locked_until=None,
    )
    audit_row = SimpleNamespace(
        event='profile.update',
        success=True,
        error_code=None,
        created_at=SimpleNamespace(isoformat=lambda: '2026-01-02T00:00:00'),
    )

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        profile_service, 'get_user_by_id', lambda _s, *, user_id: user,
    )
    monkeypatch.setattr(
        profile_service, 'count_active_mfa', lambda _s, *, user_id: 0,
    )
    monkeypatch.setattr(
        profile_service, 'list_mfa_methods', lambda _s, *, user_id: [],
    )
    monkeypatch.setattr(
        profile_service,
        'get_webauthn_credentials',
        lambda _s, *, user_id: [],
    )
    monkeypatch.setattr(
        profile_service,
        'count_remaining_recovery_codes',
        lambda _s, *, user_id: 0,
    )
    monkeypatch.setattr(
        profile_service, 'count_user_sessions', lambda _s, *, user_id: 3,
    )
    monkeypatch.setattr(
        profile_service,
        'list_recent_audit',
        lambda _s, *, user_id, limit: [audit_row],
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.admin_detail(user_id='user-1')

    assert result == {
        'profile': {
            'id': 'user-1',
            'email': 'u@example.com',
            'display_name': 'Neo',
            'locale': 'es',
            'timezone': 'UTC',
            'marketing_consent': False,
            'status': 'active',
            'created_at': '2026-01-01T00:00:00',
            'deleted_at': None,
            'email_verified_at': None,
            'failed_attempts': 0,
            'locked_until': None,
        },
        'mfa': {
            'mfa_configured': False,
            'mfa_methods': [],
            'webauthn_count': 0,
            'recovery_codes_remaining': 0,
        },
        'sessions_count': 3,
        'recent_audit': [
            {
                'event': 'profile.update',
                'success': True,
                'error_code': None,
                'created_at': '2026-01-02T00:00:00',
            },
        ],
    }
