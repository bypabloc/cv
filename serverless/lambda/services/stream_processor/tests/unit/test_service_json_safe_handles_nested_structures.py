"""Service stream_service._json_safe — estructuras anidadas.

Given un dict con Decimal, listas y dicts anidados,
When se invoca _json_safe,
Then baja los Decimal a int/float recursivamente y conserva el resto.
"""

from decimal import Decimal

import pytest

pytestmark = pytest.mark.unit


def test_service_json_safe_handles_nested_structures():
    from services.stream_service import _json_safe

    # Arrange
    value = {
        'count': Decimal('5'),
        'ratio': Decimal('1.5'),
        'tags': [Decimal('1'), 'x'],
        'nested': {'inner': Decimal('3')},
    }

    # Act
    result = _json_safe(value)

    # Assert
    assert result == {
        'count': 5,
        'ratio': 1.5,
        'tags': [1, 'x'],
        'nested': {'inner': 3},
    }
