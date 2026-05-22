"""Service db_service.run_seed.

Given que el seeder del CV levanta una excepcion (DB inaccesible, YAML
invalido, schema sin migrar),
When se invoca db_service.run_seed,
Then la traduce a un ServiceError con code=5000 y error_code=SEED_FAILED.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_seed_service_raises_service_error_on_failure():
    from services.db_service import ServiceError, run_seed

    # Act
    with (
        patch(
            'services.seed_service.run_seed',
            side_effect=RuntimeError('connection refused'),
        ),
        pytest.raises(ServiceError) as exc_info,
    ):
        run_seed()

    # Assert
    assert exc_info.value.code == 5000
    assert exc_info.value.error_code == 'SEED_FAILED'
    assert 'connection refused' in exc_info.value.message
