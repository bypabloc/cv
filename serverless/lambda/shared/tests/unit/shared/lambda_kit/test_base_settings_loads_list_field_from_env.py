"""shared.lambda_kit.base_settings.BaseSettings.

Given una subclase con un campo list anotado y la env var seteada como
     CSV separado por ', ',
When se instancia,
Then el campo toma la lista resultante del split.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.base_settings import BaseSettings

pytestmark = pytest.mark.unit


def test_base_settings_loads_list_field_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv('HOSTS', 'a.com, b.com, c.com')

    class _Config(BaseSettings):
        hosts: list[str] = []  # noqa: RUF012 - default de prueba de BaseSettings

    # Act
    config = _Config()

    # Assert
    assert config.hosts == ['a.com', 'b.com', 'c.com']
