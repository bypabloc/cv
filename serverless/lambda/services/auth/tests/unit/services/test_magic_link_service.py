"""MagicLinkService — happy + sad path."""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_generate_and_persist_returns_plain_and_hash(monkeypatch):
    from services import magic_link_service
    from shared.db.models import AuthLinkKind

    monkeypatch.setattr(magic_link_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        magic_link_service, 'generate_opaque_token', lambda: 'PLAIN_TOKEN',
    )
    monkeypatch.setattr(magic_link_service, 'hash_token', lambda _p: b'H')
    monkeypatch.setattr(magic_link_service, 'insert_magic_link', MagicMock())

    svc = magic_link_service.MagicLinkService(app_config=object())
    plain, h = svc.generate_and_persist(
        user_id='user-1', kind=AuthLinkKind.REGISTER,
    )

    assert plain == 'PLAIN_TOKEN'
    assert h == b'H'


def test_verify_returns_none_when_not_found(monkeypatch):
    from services import magic_link_service

    monkeypatch.setattr(magic_link_service, 'db_session', _fake_session)
    monkeypatch.setattr(magic_link_service, 'hash_token', lambda _p: b'H')
    monkeypatch.setattr(
        magic_link_service, 'consume_magic_link', lambda *_a, **_kw: None,
    )

    svc = magic_link_service.MagicLinkService(app_config=object())

    assert svc.verify(plain='X' * 40) is None


def test_verify_returns_row_when_found(monkeypatch):
    from services import magic_link_service

    fake_row = MagicMock(user_id='user-y')
    monkeypatch.setattr(magic_link_service, 'db_session', _fake_session)
    monkeypatch.setattr(magic_link_service, 'hash_token', lambda _p: b'H')
    monkeypatch.setattr(
        magic_link_service, 'consume_magic_link', lambda *_a, **_kw: fake_row,
    )

    svc = magic_link_service.MagicLinkService(app_config=object())

    assert svc.verify(plain='X' * 40) is fake_row
