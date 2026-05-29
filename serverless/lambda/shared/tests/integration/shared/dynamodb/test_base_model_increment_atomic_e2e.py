"""
Given la tabla de buckets de rate-limit creada por el ORM,
When RateLimitBucketItem.increment hace ADD atomico varias veces,
Then el counter acumula y set_fields actualiza expires_at en el mismo
     UpdateExpression.
"""

from __future__ import annotations

import pytest
from shared.dynamodb.models import RateLimitBucketItem

pytestmark = pytest.mark.integration


def test_base_model_increment_atomic_e2e(dynamodb_tables: None) -> None:
    """increment() acumula el counter y setea expires_at a la vez."""
    # Arrange / Act
    first = RateLimitBucketItem.increment(
        'bucket-x',
        set_fields={'expires_at': 1_720_000_000},
        count=1,
    )
    second = RateLimitBucketItem.increment(
        'bucket-x',
        set_fields={'expires_at': 1_720_000_500},
        count=3,
    )
    stored = RateLimitBucketItem.get('bucket-x')

    # Assert
    assert first['count'] == 1
    assert second['count'] == 4
    assert stored is not None
    assert stored.count == 4
    assert stored.expires_at == 1_720_000_500
