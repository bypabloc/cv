"""publish.status shapea el run mas reciente del workflow.

Given latest_run devuelve un run completed/success,
When se invoca publish_service.status,
Then devuelve {status, conclusion, url, created_at, ref} exactos.
"""

from unittest.mock import MagicMock


def test_publish_status_ok(monkeypatch):
    from services import publish_service

    monkeypatch.setattr(
        publish_service.app_config, 'environment', 'dev',
    )
    monkeypatch.setattr(
        publish_service,
        'get_secret_by_name',
        lambda *_a, **_k: 'fake-pat',
    )
    run = {
        'status': 'completed',
        'conclusion': 'success',
        'html_url': 'https://github.com/bypabloc/cv/actions/runs/42',
        'created_at': '2026-06-09T10:00:00Z',
    }
    latest_mock = MagicMock(return_value=run)
    monkeypatch.setattr(publish_service, 'latest_run', latest_mock)

    result = publish_service.status()

    assert result == {
        'status': 'completed',
        'conclusion': 'success',
        'url': 'https://github.com/bypabloc/cv/actions/runs/42',
        'created_at': '2026-06-09T10:00:00Z',
        'ref': 'dev',
    }
    latest_mock.assert_called_once_with(
        'fake-pat', 'bypabloc/cv', 'deploy-apps.yml', 'dev',
    )
