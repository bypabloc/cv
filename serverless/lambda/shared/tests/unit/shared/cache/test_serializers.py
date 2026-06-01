"""Tests para shared.cache.serializers."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from shared.cache.serializers import SerializationError, deserialize, serialize

pytestmark = pytest.mark.unit


class TestSerialize:
    """serialize - convierte Python value a (string, encoding)."""

    @pytest.mark.parametrize(
        ('value', 'expected_enc'),
        [
            ({'a': 1}, 'json'),
            ([1, 2, 3], 'json'),
            ('hello', 'json'),
            (42, 'json'),
            (True, 'json'),
            (None, 'json'),
            (b'binary', 'bytes_b64'),
        ],
    )
    def test_when_json_safe_or_bytes_then_correct_encoding(
        self, value: object, expected_enc: str
    ) -> None:
        """Given value Python, When serialize, Then retorna encoding correcto."""
        _, encoding = serialize(value)

        assert encoding == expected_enc

    def test_when_not_serializable_then_raises(self) -> None:
        """
        Given object no JSON-safe,
        When serialize,
        Then SerializationError.
        """
        class NotSerializable:
            pass

        with pytest.raises(SerializationError):
            serialize(NotSerializable())


class TestRoundtrip:
    """serialize -> deserialize debe retornar el valor original."""

    @pytest.mark.parametrize(
        'value',
        [
            {'a': 1, 'b': 'two'},
            [1, 2, 3, 'four'],
            'simple string',
            42,
            3.14,
            True,
            None,
            b'binary bytes',
        ],
    )
    def test_roundtrip_preserves_value(self, value: object) -> None:
        """Given value, When serialize -> deserialize, Then mismo valor."""
        ser_value, encoding = serialize(value)
        result = deserialize(ser_value, encoding)

        assert result == value


class TestDynamoDBTypes:
    """
    Tipos custom de DynamoDB (Decimal, set, bytes anidado) deben serializarse
    sin TypeError. Reasons: boto3 Resource API retorna numericos como
    `Decimal`, lo que rompia el cache de `get_ip_rule`.
    """

    def test_when_decimal_integer_then_serializes_as_int(self) -> None:
        """Given Decimal(3), When serialize, Then JSON '3' (int)."""
        ser, enc = serialize(Decimal('3'))
        assert enc == 'json'
        assert json.loads(ser) == 3

    def test_when_decimal_float_then_serializes_as_float(self) -> None:
        """Given Decimal('3.5'), When serialize, Then JSON 3.5 (float)."""
        ser, enc = serialize(Decimal('3.5'))
        assert enc == 'json'
        assert json.loads(ser) == 3.5

    def test_when_dict_with_decimal_nested_then_serializes(self) -> None:
        """
        Given dict con Decimal anidado (el caso real del rate-limit IP rule),
        When serialize,
        Then JSON con int en lugar de Decimal.
        """
        value = {'ip': '1.2.3.4', 'count': Decimal('5'), 'rate': Decimal('0.5')}
        ser, enc = serialize(value)
        assert enc == 'json'
        result = deserialize(ser, enc)
        assert result == {'ip': '1.2.3.4', 'count': 5, 'rate': 0.5}

    def test_when_set_then_serializes_as_list(self) -> None:
        """Given set, When serialize, Then JSON array (set -> list)."""
        value = {1, 2, 3}
        ser, enc = serialize(value)
        assert enc == 'json'
        assert sorted(deserialize(ser, enc)) == [1, 2, 3]


class TestDeserialize:
    """deserialize - error paths."""

    def test_when_unknown_encoding_then_raises(self) -> None:
        """Given encoding desconocido, When deserialize, Then SerializationError."""
        with pytest.raises(SerializationError):
            deserialize('x', 'unknown_encoding')

    def test_when_invalid_json_then_raises(self) -> None:
        """Given JSON malformado, When deserialize encoding=json, Then SerializationError."""
        with pytest.raises(SerializationError):
            deserialize('{not valid json', 'json')

    def test_when_invalid_base64_then_raises(self) -> None:
        """Given base64 invalido, When deserialize, Then SerializationError."""
        with pytest.raises(SerializationError):
            deserialize('!!!', 'bytes_b64')
