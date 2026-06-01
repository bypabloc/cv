"""require_admin_user — caller es admin.

Given un user cuyo email esta en la whitelist admin,
When se invoca require_admin_user,
Then no levanta nada y no registra ningun intento de audit.
"""

from types import SimpleNamespace


def test_admin_require_admin_user_ok(monkeypatch):
    from services import admin_service

    calls = {'require_admin': 0, 'audit': 0}

    def fake_require_admin(_email):
        calls['require_admin'] += 1

    class _FakeAudit:
        def __init__(self, _config):
            pass

        def log_attempt(self, **_kwargs):
            calls['audit'] += 1

    monkeypatch.setattr(admin_service, 'require_admin', fake_require_admin)
    monkeypatch.setattr(admin_service, 'AuditAdminService', _FakeAudit)

    user = SimpleNamespace(id='admin-1', email='admin@example.com')
    admin_service.require_admin_user(user)

    assert calls['require_admin'] == 1
    assert calls['audit'] == 0
