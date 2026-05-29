"""require_admin_user — caller NO es admin.

Given un user cuyo email NO esta en la whitelist admin,
When se invoca require_admin_user,
Then registra el intento fallido (log_attempt) y re-levanta AdminAuthzError.
"""

from types import SimpleNamespace

import pytest


def test_admin_require_admin_user_non_admin_logs_and_raises(monkeypatch):
    from services import admin_service
    from shared.auth.admin import AdminAuthzError

    calls = {'audit': None}

    def fake_require_admin(_email):
        raise AdminAuthzError('not admin')

    class _FakeAudit:
        def __init__(self, _config):
            pass

        def log_attempt(self, *, admin_user_id, action, success, ip,
                        user_agent):
            calls['audit'] = {
                'admin_user_id': admin_user_id,
                'action': action,
                'success': success,
            }

    monkeypatch.setattr(admin_service, 'require_admin', fake_require_admin)
    monkeypatch.setattr(admin_service, 'AuditAdminService', _FakeAudit)

    user = SimpleNamespace(id='user-1', email='visitor@example.com')

    with pytest.raises(AdminAuthzError):
        admin_service.require_admin_user(user, audit_action='admin.disable')

    assert calls['audit'] == {
        'admin_user_id': 'user-1',
        'action': 'admin.disable',
        'success': False,
    }
