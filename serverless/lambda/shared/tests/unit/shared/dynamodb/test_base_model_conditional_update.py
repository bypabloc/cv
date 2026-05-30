"""
Given un item existente,
When se llama .conditional_update() con una condicion,
Then actualiza solo si la condicion pasa, sino devuelve None (AC-4).
"""

from __future__ import annotations

import pytest
from shared.dynamodb.models.cache import CacheItem


def _seed_lock(holder: str = 'holder-1') -> None:
    """Persiste un lock con un holder conocido."""
    CacheItem(
        cache_key='lock:job',
        value=holder,
        encoding='lock',
        expires_at=1715000015,
        stale_until=1715000015,
    ).save()


@pytest.mark.usefixtures('dynamodb_tables')
def test_conditional_update_applies_when_condition_passes() -> None:
    """Actualiza si la condicion sobre el holder se cumple."""
    # Arrange
    _seed_lock('holder-1')

    # Act
    result = CacheItem.conditional_update(
        'lock:job',
        condition='#value = :holder',
        condition_values={':holder': 'holder-1'},
        condition_names={'#value': 'value'},
        encoding='released',
    )

    # Assert
    assert result is not None
    assert result.encoding == 'released'


@pytest.mark.usefixtures('dynamodb_tables')
def test_conditional_update_returns_none_when_condition_fails() -> None:
    """Devuelve None (sin escribir) si la condicion no se cumple."""
    # Arrange
    _seed_lock('holder-1')

    # Act
    result = CacheItem.conditional_update(
        'lock:job',
        condition='#value = :holder',
        condition_values={':holder': 'otro-holder'},
        condition_names={'#value': 'value'},
        encoding='released',
    )

    # Assert
    assert result is None
    # El item no cambio.
    assert CacheItem.get('lock:job').encoding == 'lock'
