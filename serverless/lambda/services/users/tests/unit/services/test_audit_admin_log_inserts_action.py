"""AuditAdminService.log — inserta un row de admin action.

Given una accion admin con target,
When se invoca log,
Then delega a insert_admin_action con admin_user_id/target_user_id como str.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_audit_admin_log_inserts_action(monkeypatch):
    from services import audit_admin_service

    fake_session = MagicMock()
    calls = {}

    def fake_insert(_session, *, admin_user_id, target_user_id, action,
                    meta_data, ip, user_agent):
        calls['admin_user_id'] = admin_user_id
        calls['target_user_id'] = target_user_id
        calls['action'] = action

    monkeypatch.setattr(
        audit_admin_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        audit_admin_service, 'insert_admin_action', fake_insert,
    )

    svc = audit_admin_service.AuditAdminService(app_config=object())
    svc.log(
        admin_user_id='admin-1',
        target_user_id='user-2',
        action='admin.disable',
    )

    assert calls['admin_user_id'] == 'admin-1'
    assert calls['target_user_id'] == 'user-2'
    assert calls['action'] == 'admin.disable'
