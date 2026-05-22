"""Util base_settings.BaseSettings — validador load_ sin campo.

Given una subclase con un metodo load_<campo> cuyo <campo> no existe como
     atributo,
When se construye la instancia,
Then _apply_custom_validators no aplica ese validador (rama hasattr False).
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_skips_validator_without_field():
    from utils.base_settings import BaseSettings

    class _OrphanValidator(BaseSettings):
        stage: str = 'dev'

        def load_ghost(self, value: object) -> object:
            # 'ghost' no existe como campo -> el validador no se aplica.
            raise AssertionError('load_ghost no debe invocarse')

    # Arrange + Act
    with patch.dict(os.environ, {'STAGE': 'prod'}):
        settings = _OrphanValidator()

    # Assert
    assert settings.stage == 'prod'
    assert hasattr(settings, 'ghost') is False
