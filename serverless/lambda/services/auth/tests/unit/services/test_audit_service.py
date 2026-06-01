"""AuditService — happy + sad path."""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_log_inserts_event_with_all_fields(monkeypatch):
    from services import audit_service

    fake_insert = MagicMock()
    monkeypatch.setattr(audit_service, 'db_session', _fake_session)
    monkeypatch.setattr(audit_service, 'insert_audit_event', fake_insert)

    svc = audit_service.AuditService(app_config=object())
    svc.log(
        event='register.start',
        success=True,
        user_id='user-1',
        ip='203.0.113.10',
        user_agent='pytest',
        niche='fintech',
    )

    fake_insert.assert_called_once()
    kwargs = fake_insert.call_args.kwargs
    assert kwargs['event'] == 'register.start'
    assert kwargs['success'] is True
    assert kwargs['user_id'] == 'user-1'
    assert kwargs['niche'] == 'fintech'


def test_log_supports_failure_event(monkeypatch):
    from services import audit_service

    fake_insert = MagicMock()
    monkeypatch.setattr(audit_service, 'db_session', _fake_session)
    monkeypatch.setattr(audit_service, 'insert_audit_event', fake_insert)

    svc = audit_service.AuditService(app_config=object())
    svc.log(
        event='login.start',
        success=False,
        error_code='EMAIL_NOT_FOUND',
        ip='203.0.113.10',
    )

    kwargs = fake_insert.call_args.kwargs
    assert kwargs['success'] is False
    assert kwargs['error_code'] == 'EMAIL_NOT_FOUND'
    assert kwargs['user_id'] is None
