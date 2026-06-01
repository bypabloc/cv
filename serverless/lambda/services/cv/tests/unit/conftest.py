"""Fixtures unit del Lambda `cv`.

`cv_service` ahora decora cada funcion con `@cached` (DynamoDB). En unit
NO hay DynamoDB: este fixture autouse hace el cache TRANSPARENTE (cada
llamada es MISS -> recompute via el repository), asi los tests de
delegacion/errores existentes siguen probando la logica real sin tocar
AWS. El comportamiento de HIT se prueba aparte (test dedicado que mockea
`get_entry` con una entrada FRESH).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _cache_transparent(monkeypatch):
    """Fuerza MISS en `@cached`: recompute siempre, sin tocar DynamoDB."""
    fake_cache = MagicMock()
    fake_cache.get_entry.return_value = None  # MISS -> classify = MISS
    fake_cache.table = 'cv-cache-test'
    fake_cache.set.return_value = None
    monkeypatch.setattr(
        'shared.cache.decorator.DynamoDBCache', lambda: fake_cache
    )
    monkeypatch.setattr(
        'shared.cache.decorator.acquire_lock',
        lambda *a, **k: 'test-holder',
    )
    monkeypatch.setattr(
        'shared.cache.decorator.release_lock', lambda *a, **k: None
    )
