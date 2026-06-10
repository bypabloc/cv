"""Service db_service.run_seed.

Given el seeder del CV (seed_service.run_seed),
When se invoca db_service.run_seed,
Then delega en el seeder pasando source y confirm_overwrite, y
devuelve su resultado sin transformarlo.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_seed_service_delegates_to_seed_service():
    from services.db_service import run_seed

    # Arrange
    expected = {'seeded': True, 'counts': {'profile': 1, 'experiences': 9}}

    # Act
    with patch(
        'services.seed_service.run_seed',
        return_value=expected,
    ) as seed_mock:
        result = run_seed(
            source='s3://portfolio-db-backups-dev/history/2026-06-10/',
            confirm_overwrite=True,
        )

    # Assert
    assert result == expected
    assert seed_mock.call_args.kwargs == {
        'source': 's3://portfolio-db-backups-dev/history/2026-06-10/',
        'confirm_overwrite': True,
    }
