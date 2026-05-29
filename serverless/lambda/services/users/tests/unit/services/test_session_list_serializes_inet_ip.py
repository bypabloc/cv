"""SessionService.list_for_user — la IP INET sale como str serializable.

Given una sesion cuyo `row.ip` es un ipaddress.IPv4Address (lo que devuelve
     psycopg3 para una columna INET),
When se invoca list_for_user,
Then el dict resultante trae `ip` como str y es json.dumps-eable.

Guard de regresion: `'ip': row.ip` (crudo) metia un IPv4Address al dict y
`json.dumps` reventaba con `TypeError: Object of type IPv4Address is not JSON
serializable` -> status.list-sessions devolvia HTTP 500.
"""

import json
from contextlib import contextmanager
from ipaddress import IPv4Address, IPv6Address
from types import SimpleNamespace
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def _row(*, sid, ip):
    return SimpleNamespace(
        id=sid,
        device_info={'os': 'linux'},
        ip=ip,
        country='CL',
        family_id='fam-1',
        created_at=SimpleNamespace(isoformat=lambda: '2026-01-01T00:00:00'),
        last_active_at=SimpleNamespace(
            isoformat=lambda: '2026-01-02T00:00:00',
        ),
    )


def test_session_list_for_user_serializes_inet_ip(monkeypatch):
    from services import session_service

    fake_session = MagicMock()
    rows = [
        _row(sid='sess-v4', ip=IPv4Address('203.0.113.5')),
        _row(sid='sess-v6', ip=IPv6Address('2001:db8::1')),
        _row(sid='sess-null', ip=None),
    ]

    monkeypatch.setattr(
        session_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        session_service, 'list_user_sessions', lambda _s, *, user_id: rows,
    )

    svc = session_service.SessionService(app_config=object())
    result = svc.list_for_user(user_id='user-1', current_family_id='fam-1')

    assert result[0]['ip'] == '203.0.113.5'
    assert result[1]['ip'] == '2001:db8::1'
    assert result[2]['ip'] is None

    # El payload completo debe ser JSON-serializable (lo que fallaba en prod).
    assert json.dumps(result) is not None
