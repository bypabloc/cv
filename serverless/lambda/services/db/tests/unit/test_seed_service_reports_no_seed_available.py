"""Service db_service.run_seed.

Given que no existe un seed migrado al schema unificado de shared/db/,
When se invoca run_seed,
Then reporta honestamente que no hay seed disponible (sin inventar data).
"""

import pytest

pytestmark = pytest.mark.unit


def test_seed_service_reports_no_seed_available():
    from services.db_service import run_seed

    # Act
    result = run_seed()

    # Assert
    assert result == {
        'seeded': False,
        'reason': (
            'no hay seed disponible para el schema unificado de '
            'shared/db/ — el seed legacy de db/cv/ no esta migrado'
        ),
    }
