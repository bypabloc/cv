"""publish.status traduce GithubApiError a ServiceError 5200.

Given GitHub falla al listar los runs,
When se invoca publish_service.status,
Then ServiceError 5200 GITHUB_API_ERROR.
"""

from unittest.mock import MagicMock

import pytest


def test_publish_status_github_error(monkeypatch):
    from services import publish_service
    from services._errors import ServiceError
    from shared.http.github import GithubApiError

    monkeypatch.setattr(
        publish_service.app_config, 'environment', 'dev',
    )
    monkeypatch.setattr(
        publish_service,
        'get_secret_by_name',
        lambda *_a, **_k: 'fake-pat',
    )
    monkeypatch.setattr(
        publish_service,
        'latest_run',
        MagicMock(side_effect=GithubApiError('GitHub runs HTTP 500')),
    )

    with pytest.raises(ServiceError) as exc:
        publish_service.status()

    assert exc.value.code == 5200
    assert exc.value.error_code == 'GITHUB_API_ERROR'
