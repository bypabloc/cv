"""AuditService.log es best-effort: un fallo de Neon NO propaga.

Given que db_session/insert lanza (Neon caida, tabla inexistente),
When se invoca AuditService.log,
Then NO propaga la excepcion (el flujo de auth no debe convertirse en 500
     por un fallo de auditoria).

Guard de regresion: el docstring prometia best-effort pero el body no
tenia try/except, asi que un fallo de Neon abortaba el login/register.
"""

from types import SimpleNamespace


def test_audit_log_swallows_neon_failure(monkeypatch):
    from services import audit_service

    def _boom():
        raise RuntimeError('neon down')

    # db_session() falla al entrar al context manager.
    monkeypatch.setattr(audit_service, 'db_session', _boom)

    svc = audit_service.AuditService(SimpleNamespace())

    # No debe propagar: si lanza, el test falla.
    svc.log(event='login.start', success=True, user_id='user-1')
