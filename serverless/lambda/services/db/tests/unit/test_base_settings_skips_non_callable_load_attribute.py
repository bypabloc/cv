"""Util base_settings.BaseSettings — atributo load_ no invocable.

Given una subclase con un atributo de clase load_<algo> que NO es
     callable (un string),
When se construye la instancia,
Then _apply_custom_validators lo ignora sin fallar.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_base_settings_skips_non_callable_load_attribute():
    from utils.base_settings import BaseSettings

    class _NonCallableLoad(BaseSettings):
        stage: str = 'dev'
        # load_marker no es un metodo: es un string -> debe ignorarse.
        load_marker = 'not-a-method'

    # Arrange + Act
    with patch.dict(os.environ, {'STAGE': 'prod'}):
        settings = _NonCallableLoad()

    # Assert
    assert settings.stage == 'prod'
    assert settings.load_marker == 'not-a-method'
