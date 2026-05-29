"""
Given un Item de DynamoDB con un atributo numerico Decimal,
When se lee via BaseModel._from_item(),
Then el modelo expone ese campo como int/float, nunca Decimal (AC-2).
"""

from __future__ import annotations

from decimal import Decimal

from shared.dynamodb.models import RateLimitBucketItem, TrackingEventItem


def test_from_item_converts_integer_decimal_to_int() -> None:
    """Un Decimal entero se baja a int."""
    # Arrange
    raw = {
        'bucket_key': 'ip#1.2.3.4#endpoint#/contact#window#100',
        'count': Decimal('7'),
        'turnstile_tokens': Decimal('2'),
        'expires_at': Decimal('1715000000'),
    }

    # Act
    model = RateLimitBucketItem._from_item(raw)

    # Assert
    assert model.count == 7
    assert isinstance(model.count, int)
    assert model.turnstile_tokens == 2
    assert model.expires_at == 1715000000


def test_from_item_converts_nested_decimal_in_map() -> None:
    """Los Decimal anidados en un Map (event_props) tambien se bajan."""
    # Arrange
    raw = {
        'session_id': 's1',
        'page_id': 'p1',
        'created_at': '2026-05-21T10:00:00+00:00',
        'expires_at': Decimal('1720000000'),
        'page_url': 'https://x.com',
        'event_id': 'e1',
        'event_type_id': 'page_view',
        'event_props': {'scroll_pct': Decimal('80'), 'count': Decimal('3')},
    }

    # Act
    model = TrackingEventItem._from_item(raw)

    # Assert
    assert model.event_props == {'scroll_pct': 80, 'count': 3}
    assert model.expires_at == 1720000000
