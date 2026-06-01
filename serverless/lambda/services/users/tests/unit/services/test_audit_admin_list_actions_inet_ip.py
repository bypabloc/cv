"""AuditAdminService.list_actions — la IP INET sale como str serializable.

Given un row de admin action cuyo `row.ip` es un ipaddress.IPv4Address (lo
     que devuelve psycopg3 para la columna INET `auth_user_admin_actions.ip`),
When se invoca list_actions,
Then el dict trae `ip` como str y el payload es json.dumps-eable.

Guard de regresion: mismo bug que status.list-sessions. `'ip': row.ip` crudo
metia un IPv4Address al dict -> json.dumps reventaba con TypeError.
"""

import json
from contextlib import contextmanager
from ipaddress import IPv4Address
from types import SimpleNamespace
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_audit_admin_list_actions_serializes_inet_ip(monkeypatch):
    from services import audit_admin_service

    fake_session = MagicMock()
    rows = [
        SimpleNamespace(
            id='action-1',
            admin_user_id='admin-1',
            target_user_id='user-2',
            action='admin.disable',
            meta_data={'reason': 'spam'},
            ip=IPv4Address('203.0.113.9'),
            created_at=SimpleNamespace(
                isoformat=lambda: '2026-01-01T00:00:00',
            ),
        ),
        SimpleNamespace(
            id='action-2',
            admin_user_id='admin-1',
            target_user_id=None,
            action='admin.list-users',
            meta_data={},
            ip=None,
            created_at=SimpleNamespace(
                isoformat=lambda: '2026-01-01T00:01:00',
            ),
        ),
    ]

    monkeypatch.setattr(
        audit_admin_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        audit_admin_service,
        'list_admin_actions',
        lambda _s, *, from_date, to_date, page_size, cursor: rows,
    )

    svc = audit_admin_service.AuditAdminService(app_config=object())
    result = svc.list_actions()

    assert result[0]['ip'] == '203.0.113.9'
    assert result[1]['ip'] is None
    assert json.dumps(result) is not None
