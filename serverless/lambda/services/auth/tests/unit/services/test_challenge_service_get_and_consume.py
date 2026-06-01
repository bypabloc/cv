"""ChallengeService.get_and_consume lee + borra el challenge (single-use).

Given un Item presente en DDB,
When se invoca get_and_consume,
Then deserializa el state, borra el row y devuelve {user_id, kind, state}.
"""

import json
from unittest.mock import MagicMock


def test_challenge_service_get_and_consume_atomic(monkeypatch):
    from services import challenge_service

    fake_table = MagicMock()
    fake_table.get_item.return_value = {
        'Item': {
            'challenge_id': 'ch-1',
            'user_id': 'user-1',
            'kind': 'login',
            'state': json.dumps({'opaque': 2}),
        },
    }
    monkeypatch.setattr(
        challenge_service,
        'get_table',
        lambda _name: fake_table,
    )

    cfg = MagicMock(webauthn_challenges_table_name='portfolio-webauthn-test')
    svc = challenge_service.ChallengeService(cfg)
    result = svc.get_and_consume(challenge_id='ch-1')

    assert result == {
        'user_id': 'user-1',
        'kind': 'login',
        'state': {'opaque': 2},
    }
    fake_table.delete_item.assert_called_once_with(Key={'challenge_id': 'ch-1'})


def test_challenge_service_get_and_consume_missing_returns_none(monkeypatch):
    from services import challenge_service

    fake_table = MagicMock()
    fake_table.get_item.return_value = {}
    monkeypatch.setattr(
        challenge_service,
        'get_table',
        lambda _name: fake_table,
    )

    cfg = MagicMock(webauthn_challenges_table_name='portfolio-webauthn-test')
    svc = challenge_service.ChallengeService(cfg)
    result = svc.get_and_consume(challenge_id='gone')

    assert result is None
    fake_table.delete_item.assert_not_called()
