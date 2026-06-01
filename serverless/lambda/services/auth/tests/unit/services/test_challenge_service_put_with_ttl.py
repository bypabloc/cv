"""ChallengeService.put persiste el challenge con expires_at = now + 300.

Given un challenge,
When se invoca put,
Then PutItem recibe el state serializado + expires_at = created_at + 300.
"""

from unittest.mock import MagicMock


def test_challenge_service_put_with_ttl(monkeypatch):
    from services import challenge_service

    fake_table = MagicMock()
    monkeypatch.setattr(
        challenge_service,
        'get_table',
        lambda _name: fake_table,
    )

    cfg = MagicMock(webauthn_challenges_table_name='portfolio-webauthn-test')
    svc = challenge_service.ChallengeService(cfg)
    svc.put(
        challenge_id='ch-1',
        user_id='user-1',
        kind='register',
        state={'opaque': 1},
    )

    item = fake_table.put_item.call_args.kwargs['Item']
    assert item['challenge_id'] == 'ch-1'
    assert item['user_id'] == 'user-1'
    assert item['kind'] == 'register'
    assert item['expires_at'] == item['created_at'] + 300
