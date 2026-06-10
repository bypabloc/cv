"""publish.dispatch traduce GithubApiError a ServiceError 5200.

Given GitHub rechaza el dispatch (GithubApiError),
When se invoca publish_service.dispatch,
Then ServiceError 5200 GITHUB_API_ERROR SIN el token en el mensaje.
"""

from unittest.mock import MagicMock

import pytest


def test_publish_dispatch_github_error(monkeypatch):
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
        'dispatch_workflow',
        MagicMock(side_effect=GithubApiError('GitHub dispatch HTTP 422')),
    )

    with pytest.raises(ServiceError) as exc:
        publish_service.dispatch()

    assert exc.value.code == 5200
    assert exc.value.error_code == 'GITHUB_API_ERROR'
    assert 'fake-pat' not in exc.value.message
