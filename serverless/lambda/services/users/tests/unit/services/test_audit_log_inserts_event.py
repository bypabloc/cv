"""AuditService.log — inserta un evento en auth_audit_log.

Given un evento de operacion,
When se invoca log,
Then delega a insert_audit_event con event/success/user_id correctos.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_audit_log_inserts_event(monkeypatch):
    from services import audit_service

    fake_session = MagicMock()
    calls = {}

    def fake_insert(_session, *, event, success, user_id, error_code, ip,
                    user_agent, niche, meta_data):
        calls['event'] = event
        calls['success'] = success
        calls['user_id'] = user_id

    monkeypatch.setattr(
        audit_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(audit_service, 'insert_audit_event', fake_insert)

    svc = audit_service.AuditService(app_config=object())
    svc.log(event='profile.update', success=True, user_id='user-1')

    assert calls['event'] == 'profile.update'
    assert calls['success'] is True
    assert calls['user_id'] == 'user-1'
