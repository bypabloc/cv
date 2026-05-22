"""
Given DATABASE_URL seteada en el entorno con esquema postgresql://,
When resolve_database_url corre,
Then devuelve la URL normalizada al driver psycopg v3.
"""

from __future__ import annotations

import pytest
from shared.db.url import resolve_database_url

pytestmark = pytest.mark.integration


def test_resolve_url_from_env_e2e(monkeypatch: pytest.MonkeyPatch) -> None:
    """DATABASE_URL del entorno se normaliza a postgresql+psycopg://."""
    # Arrange
    monkeypatch.setenv(
        'DATABASE_URL', 'postgresql://user:pw@host:5432/portfolio'
    )
    monkeypatch.delenv('SSM_NEON_URL_PATH', raising=False)

    # Act
    url = resolve_database_url()

    # Assert
    assert url == 'postgresql+psycopg://user:pw@host:5432/portfolio'
