"""Util base_settings.BaseSettings — to_dict y to_json.

Given una instancia de BaseSettings con un campo cargado,
When se invocan to_dict y to_json,
Then to_dict devuelve los atributos publicos como dict y to_json el mismo
     contenido serializado a string JSON.
"""

import json
import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_serializes_to_dict_and_json():
    from utils.base_settings import BaseSettings

    class _SerializableSettings(BaseSettings):
        stage: str = 'dev'

    # Arrange
    with patch.dict(os.environ, {'STAGE': 'prod'}):
        settings = _SerializableSettings()

    # Act
    as_dict = settings.to_dict()
    as_json = settings.to_json()

    # Assert
    assert as_dict == {'stage': 'prod'}
    assert json.loads(as_json) == {'stage': 'prod'}
