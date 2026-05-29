"""AuditAdminService.list_actions — serializa los rows de admin actions.

Given un row de admin action en Neon,
When se invoca list_actions,
Then devuelve un dict serializado con id/action/metadata/created_at.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_audit_admin_list_actions_serializes_rows(monkeypatch):
    from services import audit_admin_service

    fake_session = MagicMock()
    row = SimpleNamespace(
        id='action-1',
        admin_user_id='admin-1',
        target_user_id='user-2',
        action='admin.disable',
        meta_data={'reason': 'spam'},
        ip='1.1.1.1',
        created_at=SimpleNamespace(isoformat=lambda: '2026-01-01T00:00:00'),
    )

    monkeypatch.setattr(
        audit_admin_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        audit_admin_service,
        'list_admin_actions',
        lambda _s, *, from_date, to_date, page_size, cursor: [row],
    )

    svc = audit_admin_service.AuditAdminService(app_config=object())
    result = svc.list_actions()

    assert result == [
        {
            'id': 'action-1',
            'admin_user_id': 'admin-1',
            'target_user_id': 'user-2',
            'action': 'admin.disable',
            'metadata': {'reason': 'spam'},
            'ip': '1.1.1.1',
            'created_at': '2026-01-01T00:00:00',
        },
    ]
