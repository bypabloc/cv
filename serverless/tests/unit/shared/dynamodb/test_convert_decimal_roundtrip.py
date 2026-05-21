"""
Given valores Python y de DynamoDB,
When se convierten con _convert,
Then los tipos se mapean correctamente en ambas direcciones.
"""

from __future__ import annotations

from decimal import Decimal

from shared.dynamodb._convert import from_dynamodb, is_empty, to_dynamodb


def test_to_dynamodb_converts_float_to_decimal() -> None:
    """to_dynamodb baja float a Decimal (DynamoDB rechaza float nativo)."""
    assert to_dynamodb(3.5) == Decimal('3.5')


def test_to_dynamodb_keeps_bool_as_bool() -> None:
    """to_dynamodb NO convierte bool (es subclase de int)."""
    assert to_dynamodb(True) is True
    assert to_dynamodb(False) is False


def test_to_dynamodb_converts_nested_float_in_dict_and_list() -> None:
    """to_dynamodb aplica recursivo sobre dict y list."""
    result = to_dynamodb({'a': [1.5, 2], 'b': {'c': 0.25}})
    assert result == {'a': [Decimal('1.5'), 2], 'b': {'c': Decimal('0.25')}}


def test_to_dynamodb_passes_through_int_str_none() -> None:
    """to_dynamodb deja int/str/None sin cambio."""
    assert to_dynamodb(7) == 7
    assert to_dynamodb('hola') == 'hola'
    assert to_dynamodb(None) is None


def test_from_dynamodb_converts_fractional_decimal_to_float() -> None:
    """from_dynamodb sube Decimal fraccional a float."""
    assert from_dynamodb(Decimal('3.5')) == 3.5
    assert isinstance(from_dynamodb(Decimal('3.5')), float)


def test_from_dynamodb_converts_nested_decimal_in_list() -> None:
    """from_dynamodb aplica recursivo sobre list."""
    assert from_dynamodb([Decimal('1'), Decimal('2.5')]) == [1, 2.5]


def test_is_empty_true_for_none_and_empty_string() -> None:
    """is_empty es True para None y string vacio."""
    assert is_empty(None) is True
    assert is_empty('') is True


def test_is_empty_false_for_zero_false_and_collections() -> None:
    """is_empty es False para 0, False y colecciones vacias (son validos)."""
    assert is_empty(0) is False
    assert is_empty(False) is False
    assert is_empty([]) is False
    assert is_empty({}) is False
