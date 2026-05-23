"""Service cv_service — manejo de error.

Given que cv_repository levanta RepositoryError,
When se invoca cv_service,
Then la traduce a ServiceError preservando code y error_code.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_cv_service_translates_repository_error():
    from services.cv_service import ServiceError, list_projects
    from shared.db.repository import RepositoryError

    # Arrange
    repo_exc = RepositoryError(
        'connection refused',
        code=5000,
        error_code='DB_QUERY_FAILED',
    )

    # Act
    with (
        patch(
            'services.cv_service._list_projects',
            side_effect=repo_exc,
        ),
        pytest.raises(ServiceError) as exc_info,
    ):
        list_projects(niche='fintech', locale='es')

    # Assert
    assert exc_info.value.code == 5000
    assert exc_info.value.error_code == 'DB_QUERY_FAILED'
    assert exc_info.value.message == 'connection refused'
