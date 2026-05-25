"""shared.db.migrations.build_config.

Given el modulo shared/db con su alembic.ini,
When se invoca build_config,
Then devuelve un Config de Alembic con script_location apuntando al
     directorio alembic/ de shared/db.
"""

from __future__ import annotations

import pytest
from shared.db.migrations import build_config

pytestmark = pytest.mark.unit


def test_build_config_sets_script_location() -> None:
    # Act
    cfg = build_config()

    # Assert
    script_location = cfg.get_main_option('script_location')
    assert script_location is not None
    assert script_location.endswith('shared/db/alembic')
