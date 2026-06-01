"""AuditAdminService.log_attempt — registra un intento de acceso admin.

Given un intento fallido de acceso admin,
When se invoca log_attempt,
Then inserta un row con target None y meta_data {'success': False}.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_audit_admin_log_attempt_records_success_flag(monkeypatch):
    from services import audit_admin_service

    fake_session = MagicMock()
    calls = {}

    def fake_insert(_session, *, admin_user_id, target_user_id, action,
                    meta_data, ip, user_agent):
        calls['target_user_id'] = target_user_id
        calls['action'] = action
        calls['meta_data'] = meta_data

    monkeypatch.setattr(
        audit_admin_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        audit_admin_service, 'insert_admin_action', fake_insert,
    )

    svc = audit_admin_service.AuditAdminService(app_config=object())
    svc.log_attempt(
        admin_user_id='user-1', action='admin.access', success=False,
    )

    assert calls['target_user_id'] is None
    assert calls['action'] == 'admin.access'
    assert calls['meta_data'] == {'success': False}
