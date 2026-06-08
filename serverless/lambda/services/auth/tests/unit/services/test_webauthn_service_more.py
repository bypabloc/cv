"""WebauthnService — cobertura de los metodos restantes.

Cubre: list_credential_ids, build_register_options, verify_registration,
persist_credential (primer MFA revoke + no-revoke), build_login_options,
has_credentials, delete, count_active.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock
from uuid import uuid4


def _cfg():
    return MagicMock(
        webauthn_rp_id='the-full-stack.com',
        webauthn_rp_name='TFS',
        webauthn_origins=['https://the-full-stack.com'],
    )


@contextmanager
def _fake_session():
    yield MagicMock()


def test_list_credential_ids(monkeypatch):
    from services import webauthn_service

    cred = MagicMock()
    cred.credential_id = b'\x10' * 16
    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        webauthn_service,
        'get_webauthn_credentials',
        lambda _s, *, user_id: [cred],
    )

    svc = webauthn_service.WebauthnService(_cfg())
    assert svc.list_credential_ids(user_id=uuid4()) == [b'\x10' * 16]


def test_build_register_options(monkeypatch):
    from services import webauthn_service

    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        webauthn_service,
        'get_webauthn_credentials',
        lambda _s, *, user_id: [],
    )
    captured = {}

    def fake_build(**kwargs):
        captured.update(kwargs)
        return ({'opts': 1}, {'state': 1})

    monkeypatch.setattr(
        webauthn_service,
        'build_register_options',
        fake_build,
    )

    svc = webauthn_service.WebauthnService(_cfg())
    uid = uuid4()
    options, state = svc.build_register_options(
        user_id=uid,
        user_name='x@example.com',
    )

    assert options == {'opts': 1}
    assert state == {'state': 1}
    assert captured['user_id'] == uid.bytes
    assert captured['rp_id'] == 'the-full-stack.com'


def test_verify_registration(monkeypatch):
    from services import webauthn_service

    monkeypatch.setattr(
        webauthn_service,
        'verify_registration',
        lambda **_k: {'credential_id': b'\x10' * 16},
    )

    svc = webauthn_service.WebauthnService(_cfg())
    result = svc.verify_registration(state={'s': 1}, response={'id': 'x'})

    assert result == {'credential_id': b'\x10' * 16}


def test_persist_credential_first_mfa_revokes(monkeypatch):
    from services import webauthn_service

    counts = iter([0, 1])
    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    # El revoke de persist_credential usa la cuenta FUERTE (excluye email_code).
    monkeypatch.setattr(
        webauthn_service,
        'count_active_strong_mfa',
        lambda _s, *, user_id: next(counts),
    )
    monkeypatch.setattr(
        webauthn_service,
        'insert_webauthn_credential',
        lambda _s, **_k: None,
    )

    revoked = {}
    fake_session_svc = MagicMock()
    fake_session_svc.revoke_all_for_user.side_effect = lambda *, user_id: (
        revoked.update(uid=user_id)
    )
    monkeypatch.setattr(
        webauthn_service,
        'SessionService',
        lambda _c: fake_session_svc,
    )

    svc = webauthn_service.WebauthnService(_cfg())
    cred_data = {
        'credential_id': b'\x10' * 16,
        'public_key': b'\x20' * 32,
        'sign_count': 0,
        'aaguid': None,
    }
    svc.persist_credential(
        user_id='u-1',
        cred_data=cred_data,
        nickname='Mac',
    )

    assert revoked == {'uid': 'u-1'}


def test_persist_credential_not_first_no_revoke(monkeypatch):
    from services import webauthn_service

    counts = iter([1, 2])
    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        webauthn_service,
        'count_active_strong_mfa',
        lambda _s, *, user_id: next(counts),
    )
    monkeypatch.setattr(
        webauthn_service,
        'insert_webauthn_credential',
        lambda _s, **_k: None,
    )

    fake_session_svc = MagicMock()
    monkeypatch.setattr(
        webauthn_service,
        'SessionService',
        lambda _c: fake_session_svc,
    )

    svc = webauthn_service.WebauthnService(_cfg())
    cred_data = {
        'credential_id': b'\x10' * 16,
        'public_key': b'\x20' * 32,
        'sign_count': 0,
        'aaguid': None,
    }
    svc.persist_credential(user_id='u-1', cred_data=cred_data, nickname=None)

    fake_session_svc.revoke_all_for_user.assert_not_called()


def test_build_login_options(monkeypatch):
    from services import webauthn_service

    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        webauthn_service,
        'get_webauthn_credentials',
        lambda _s, *, user_id: [],
    )
    monkeypatch.setattr(
        webauthn_service,
        'build_login_options',
        lambda **_k: ({'opts': 1}, {'state': 1}),
    )

    svc = webauthn_service.WebauthnService(_cfg())
    options, state = svc.build_login_options(user_id=uuid4())

    assert options == {'opts': 1}
    assert state == {'state': 1}


def test_has_credentials(monkeypatch):
    from services import webauthn_service

    cred = MagicMock()
    cred.credential_id = b'\x10' * 16
    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        webauthn_service,
        'get_webauthn_credentials',
        lambda _s, *, user_id: [cred],
    )

    svc = webauthn_service.WebauthnService(_cfg())
    assert svc.has_credentials(user_id=uuid4()) is True


def test_delete_and_count_active(monkeypatch):
    from services import webauthn_service

    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        webauthn_service,
        'delete_webauthn_credential',
        lambda _s, *, user_id, record_id: True,
    )
    monkeypatch.setattr(
        webauthn_service,
        'count_active_mfa',
        lambda _s, *, user_id: 2,
    )

    svc = webauthn_service.WebauthnService(_cfg())
    assert svc.delete(user_id='u-1', record_id='rec-1') is True
    assert svc.count_active(user_id='u-1') == 2
