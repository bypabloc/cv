"""shared.aws re-exporta TypeDeserializer y TypeSerializer.

Given el subpaquete shared.aws,
When importo TypeDeserializer / TypeSerializer desde shared.aws,
Then son exactamente los mismos objetos que boto3.dynamodb.types y un
     deserialize round-trip basico funciona como SDK boto3 nativo.
"""

from __future__ import annotations

import pytest
from boto3.dynamodb.types import TypeDeserializer as BotoTypeDeserializer
from boto3.dynamodb.types import TypeSerializer as BotoTypeSerializer
from shared.aws import TypeDeserializer, TypeSerializer

pytestmark = pytest.mark.unit


def test_type_deserializer_is_boto3_class() -> None:
    # Arrange + Act + Assert
    assert TypeDeserializer is BotoTypeDeserializer


def test_type_serializer_is_boto3_class() -> None:
    # Arrange + Act + Assert
    assert TypeSerializer is BotoTypeSerializer


def test_type_deserializer_deserializes_string_attribute() -> None:
    # Arrange
    deserializer = TypeDeserializer()

    # Act
    result = deserializer.deserialize({'S': 'hello'})

    # Assert
    assert result == 'hello'


def test_type_deserializer_deserializes_number_as_decimal() -> None:
    # Arrange
    from decimal import Decimal

    deserializer = TypeDeserializer()

    # Act
    result = deserializer.deserialize({'N': '42'})

    # Assert
    assert result == Decimal('42')
