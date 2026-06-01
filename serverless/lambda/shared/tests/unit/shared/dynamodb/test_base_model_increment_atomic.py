"""
Given un RateLimitBucketItem,
When se llama .increment(pk, count=1, turnstile_tokens=1),
Then se suma atomicamente y devuelve los valores ALL_NEW como int (AC-3).
"""

from __future__ import annotations

import pytest
from shared.dynamodb.models.rate_limit_bucket import RateLimitBucketItem


@pytest.mark.usefixtures('dynamodb_tables')
def test_increment_creates_and_sums_counters() -> None:
    """increment() crea el bucket y suma los dos contadores."""
    # Act
    result = RateLimitBucketItem.increment(
        'ip#1.2.3.4#endpoint#/contact#window#100',
        count=1,
        turnstile_tokens=1,
    )

    # Assert
    assert result == {'count': 1, 'turnstile_tokens': 1}


@pytest.mark.usefixtures('dynamodb_tables')
def test_increment_accumulates_across_calls() -> None:
    """Llamadas sucesivas acumulan el contador."""
    # Arrange
    key = 'ip#9.9.9.9#endpoint#/track#window#200'
    RateLimitBucketItem.increment(key, count=1)
    RateLimitBucketItem.increment(key, count=1)

    # Act
    result = RateLimitBucketItem.increment(key, count=1)

    # Assert
    assert result['count'] == 3


@pytest.mark.usefixtures('dynamodb_tables')
def test_increment_returns_int_not_decimal() -> None:
    """El contador devuelto es int, no Decimal."""
    # Act
    result = RateLimitBucketItem.increment('k', count=5)

    # Assert
    assert result['count'] == 5
    assert isinstance(result['count'], int)


@pytest.mark.usefixtures('dynamodb_tables')
def test_increment_with_set_fields_writes_both() -> None:
    """increment() con set_fields suma el contador y setea el atributo."""
    # Act
    result = RateLimitBucketItem.increment(
        'k', set_fields={'expires_at': 1715000200}, count=1
    )

    # Assert
    assert result == {'count': 1}
    stored = RateLimitBucketItem.get('k')
    assert stored is not None
    assert stored.count == 1
    assert stored.expires_at == 1715000200


@pytest.mark.usefixtures('dynamodb_tables')
def test_increment_without_deltas_raises() -> None:
    """increment() sin deltas es un error de programacion."""
    # Act / Assert
    with pytest.raises(ValueError, match='delta'):
        RateLimitBucketItem.increment('k')
