"""
Given una rule de endpoint creada en DynamoDB,
When get_endpoint_rule se llama y luego la rule se borra de la tabla,
Then la 2a llamada sigue devolviendo la rule desde el cache @cached
     (el lookup es read-heavy y se cachea con ttl=60).
"""

from __future__ import annotations

import pytest
from shared.dynamodb.models import RateLimitRuleItem
from shared.rate_limit.rules import get_endpoint_rule

pytestmark = pytest.mark.integration


def test_rules_lookup_cached_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """get_endpoint_rule cachea: borrar la rule no afecta el 2o lookup."""
    # Arrange
    RateLimitRuleItem(
        rule_key='endpoint#/contact',
        kind='endpoint',
        limit=5,
        window_seconds=60,
        action='throttle',
    ).save()

    # Act
    first = get_endpoint_rule('/contact')
    # Borrar la rule en DynamoDB; el cache @cached debe seguir sirviendola.
    RateLimitRuleItem.delete('endpoint#/contact', 'endpoint')
    second = get_endpoint_rule('/contact')

    # Assert
    assert first is not None
    assert first['limit'] == 5
    assert second == first
