"""publish.status sin runs devuelve {'status': 'none'}.

Given latest_run devuelve None (workflow sin runs para el ref),
When se invoca publish_service.status,
Then devuelve {'status': 'none', 'ref': 'dev'}.
"""

from unittest.mock import MagicMock


def test_publish_status_none(monkeypatch):
    from services import publish_service

    monkeypatch.setattr(
        publish_service.app_config, 'environment', 'dev',
    )
    monkeypatch.setattr(
        publish_service,
        'get_secret_by_name',
        lambda *_a, **_k: 'fake-pat',
    )
    monkeypatch.setattr(
        publish_service, 'latest_run', MagicMock(return_value=None),
    )

    result = publish_service.status()

    assert result == {'status': 'none', 'ref': 'dev'}
