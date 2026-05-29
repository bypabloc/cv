"""Fixtures de los tests de shared.auth.

`_reset_admin_cache` (autouse) limpia el cache module-level de
`shared.auth.admin` antes y despues de cada test. Sin esto, el orden de
ejecucion cambia el resultado: un test que mockea la whitelist deja el
cache poblado y contamina al siguiente (cache hit con emails de otro
test).
"""

from __future__ import annotations

from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def _reset_admin_cache() -> Generator[None]:
    """Resetea el cache de admin emails antes y despues de cada test."""
    import shared.auth.admin as admin

    admin._CACHE.update({'emails': frozenset(), 'expires_at': 0.0})
    yield
    admin._CACHE.update({'emails': frozenset(), 'expires_at': 0.0})
