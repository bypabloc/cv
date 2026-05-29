"""CodeService — happy + sad path."""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_generate_and_persist_returns_code_and_hash(monkeypatch):
    from services import code_service
    from shared.db.models import AuthCodeKind

    monkeypatch.setattr(code_service, 'db_session', _fake_session)
    monkeypatch.setattr(code_service, 'generate_code', lambda: 'ABCDEFGH')
    monkeypatch.setattr(code_service, 'hash_code', lambda _c: b'fake-hash')
    monkeypatch.setattr(code_service, 'insert_email_code', MagicMock())

    svc = code_service.CodeService(app_config=object())
    code, code_h = svc.generate_and_persist(
        user_id='user-1',
        kind=AuthCodeKind.REGISTER,
    )

    assert code == 'ABCDEFGH'
    assert code_h == b'fake-hash'


def test_verify_returns_false_when_wrong_code(monkeypatch):
    from services import code_service
    from shared.db.models import AuthCodeKind

    monkeypatch.setattr(code_service, 'db_session', _fake_session)
    monkeypatch.setattr(code_service, 'hash_code', lambda _c: b'h')
    monkeypatch.setattr(code_service, 'compare_code', lambda **_kw: False)
    monkeypatch.setattr(
        code_service,
        'consume_email_code',
        lambda *_a, **_kw: None,
    )

    svc = code_service.CodeService(app_config=object())
    user = MagicMock(id='user-x')

    assert (
        svc.verify(user=user, kind=AuthCodeKind.REGISTER, code='WRONGSEQ')
        is False
    )


def test_verify_returns_true_when_match(monkeypatch):
    from services import code_service
    from shared.db.models import AuthCodeKind

    monkeypatch.setattr(code_service, 'db_session', _fake_session)
    monkeypatch.setattr(code_service, 'hash_code', lambda _c: b'h')
    monkeypatch.setattr(
        code_service,
        'consume_email_code',
        lambda *_a, **_kw: MagicMock(),
    )

    svc = code_service.CodeService(app_config=object())
    user = MagicMock(id='user-x')

    assert (
        svc.verify(user=user, kind=AuthCodeKind.REGISTER, code='ABCDEFGH')
        is True
    )
