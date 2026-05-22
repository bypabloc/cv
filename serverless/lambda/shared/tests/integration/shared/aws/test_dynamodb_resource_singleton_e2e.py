"""
Given el resource boto3 cacheado de shared.aws.dynamodb,
When get_resource y get_table se llaman varias veces,
Then todas reusan la MISMA instancia singleton (reduce cold start).
"""

from __future__ import annotations

import pytest
from shared.aws.dynamodb import get_resource, get_table

pytestmark = pytest.mark.integration


def test_dynamodb_resource_singleton_e2e(cache_table: str) -> None:
    """get_resource() devuelve siempre la misma instancia cacheada."""
    # Act
    resource_a = get_resource()
    resource_b = get_resource()
    table_a = get_table(cache_table)
    table_b = get_table(cache_table)

    # Assert
    assert resource_a is resource_b
    # Las Table son referencias livianas sobre el mismo resource.
    assert table_a.meta.client is table_b.meta.client
