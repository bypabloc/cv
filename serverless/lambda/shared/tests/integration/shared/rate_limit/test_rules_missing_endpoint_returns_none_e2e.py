"""
Given la tabla de rules vacia,
When get_endpoint_rule pide un endpoint sin rule,
Then devuelve None (el caller cae a los defaults DEFAULT_LIMIT/WINDOW).
"""

from __future__ import annotations

import pytest
from shared.rate_limit.rules import get_endpoint_rule

pytestmark = pytest.mark.integration


def test_rules_missing_endpoint_returns_none_e2e(
    rate_limit_tables: dict[str, str],
) -> None:
    """Un endpoint sin rule en DynamoDB devuelve None."""
    # Act
    rule = get_endpoint_rule('/no-such-endpoint')

    # Assert
    assert rule is None
