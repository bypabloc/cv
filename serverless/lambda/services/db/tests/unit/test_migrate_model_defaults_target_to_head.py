"""Modelo MigrateModel.

Given un payload sin 'target',
When se valida con MigrateModel,
Then 'target' toma el default 'head'.
"""

import pytest

pytestmark = pytest.mark.unit


def test_migrate_model_defaults_target_to_head():
    from models.db import MigrateModel

    # Act
    model = MigrateModel()

    # Assert
    assert model.target == 'head'
