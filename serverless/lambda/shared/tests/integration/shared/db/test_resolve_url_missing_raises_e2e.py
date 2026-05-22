"""
Given ni DATABASE_URL ni SSM_NEON_URL_PATH seteadas,
When resolve_database_url corre,
Then levanta RuntimeError indicando que falta la configuracion.
"""

from __future__ import annotations

import pytest
from shared.db.url import resolve_database_url

pytestmark = pytest.mark.integration


def test_resolve_url_missing_raises_e2e(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sin DATABASE_URL ni SSM_NEON_URL_PATH -> RuntimeError."""
    # Arrange
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('SSM_NEON_URL_PATH', raising=False)

    # Act / Assert
    with pytest.raises(RuntimeError, match='SSM_NEON_URL_PATH'):
        resolve_database_url()
