"""shared.core re-exporta pydantic.

Given el subpaquete shared.core,
When importo BaseModel, Field, EmailStr, field_validator,
     model_validator y ConfigDict desde shared.core,
Then son exactamente los mismos objetos que pydantic exporta y los
     services pueden usarlos sin importar pydantic directo.
"""

from __future__ import annotations

import pydantic
import pytest
from shared.core import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

pytestmark = pytest.mark.unit


def test_basemodel_is_pydantic_basemodel() -> None:
    # Arrange + Act + Assert
    assert BaseModel is pydantic.BaseModel


def test_field_is_pydantic_field() -> None:
    # Arrange + Act + Assert
    assert Field is pydantic.Field


def test_emailstr_is_pydantic_emailstr() -> None:
    # Arrange + Act + Assert
    assert EmailStr is pydantic.EmailStr


def test_field_validator_is_pydantic_field_validator() -> None:
    # Arrange + Act + Assert
    assert field_validator is pydantic.field_validator


def test_model_validator_is_pydantic_model_validator() -> None:
    # Arrange + Act + Assert
    assert model_validator is pydantic.model_validator


def test_configdict_is_pydantic_configdict() -> None:
    # Arrange + Act + Assert
    assert ConfigDict is pydantic.ConfigDict


def test_basemodel_round_trip_with_emailstr() -> None:
    # Arrange
    class User(BaseModel):
        email: EmailStr
        age: int = Field(ge=0)

    # Act
    instance = User(email='user@example.com', age=30)

    # Assert
    assert instance.email == 'user@example.com'
    assert instance.age == 30
