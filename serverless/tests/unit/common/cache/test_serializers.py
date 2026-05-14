"""Tests para common.cache.serializers."""

from __future__ import annotations

import pytest

from common.cache.serializers import SerializationError, deserialize, serialize

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
