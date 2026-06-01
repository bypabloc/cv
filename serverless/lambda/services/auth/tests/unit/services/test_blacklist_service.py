"""BlacklistService — happy + sad path (DDB ops mockeadas)."""

from types import SimpleNamespace
from unittest.mock import MagicMock


def _fake_app_config():
    return SimpleNamespace(
        jwt_blacklist_table_name='portfolio-jwt-blacklist-test'
    )


def test_put_writes_item_with_ttl(monkeypatch):
    from services import blacklist_service

    fake_table = MagicMock()
    monkeypatch.setattr(
        blacklist_service,
        'get_table',
        lambda _name: fake_table,
    )

    svc = blacklist_service.BlacklistService(_fake_app_config())
    svc.put(
        jti='jti-1',
        exp=1_700_000_000,
        user_id='user-x',
        reason='rotation',
    )

    fake_table.put_item.assert_called_once()
    item = fake_table.put_item.call_args.kwargs['Item']
    assert item['jti'] == 'jti-1'
    assert item['exp'] == 1_700_000_000
    assert item['reason'] == 'rotation'


def test_is_blacklisted_returns_false_when_not_found(monkeypatch):
    from services import blacklist_service

    fake_table = MagicMock()
    fake_table.get_item.return_value = {}
    monkeypatch.setattr(
        blacklist_service,
        'get_table',
        lambda _name: fake_table,
    )

    svc = blacklist_service.BlacklistService(_fake_app_config())

    assert svc.is_blacklisted(jti='not-there') is False


def test_is_blacklisted_returns_true_when_found(monkeypatch):
    from services import blacklist_service

    fake_table = MagicMock()
    fake_table.get_item.return_value = {'Item': {'jti': 'x'}}
    monkeypatch.setattr(
        blacklist_service,
        'get_table',
        lambda _name: fake_table,
    )

    svc = blacklist_service.BlacklistService(_fake_app_config())

    assert svc.is_blacklisted(jti='x') is True


def test_revoke_family_writes_sentinel_item(monkeypatch):
    from services import blacklist_service

    fake_table = MagicMock()
    monkeypatch.setattr(
        blacklist_service,
        'get_table',
        lambda _name: fake_table,
    )

    svc = blacklist_service.BlacklistService(_fake_app_config())
    svc.revoke_family(
        family_id='fam-1',
        user_id='user-x',
        exp=1_700_000_000,
    )

    fake_table.put_item.assert_called_once()
    item = fake_table.put_item.call_args.kwargs['Item']
    assert item['jti'] == 'fam-1'
    assert item['family_id'] == 'fam-1'
    assert item['reason'] == 'reuse'


def test_put_includes_family_id_when_provided(monkeypatch):
    from services import blacklist_service

    fake_table = MagicMock()
    monkeypatch.setattr(
        blacklist_service,
        'get_table',
        lambda _name: fake_table,
    )

    svc = blacklist_service.BlacklistService(_fake_app_config())
    svc.put(
        jti='jti-2',
        exp=1_700_000_000,
        user_id='user-x',
        reason='rotation',
        family_id='fam-1',
    )

    item = fake_table.put_item.call_args.kwargs['Item']
    assert item['family_id'] == 'fam-1'


def test_query_family_returns_jti_list(monkeypatch):
    from services import blacklist_service

    fake_table = MagicMock()
    fake_table.query.return_value = {
        'Items': [{'jti': 'a'}, {'jti': 'b'}],
    }
    monkeypatch.setattr(
        blacklist_service,
        'get_table',
        lambda _name: fake_table,
    )

    svc = blacklist_service.BlacklistService(_fake_app_config())

    assert svc.query_family(family_id='fam-1') == ['a', 'b']
