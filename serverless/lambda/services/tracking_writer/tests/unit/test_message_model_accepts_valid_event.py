"""Modelo TrackingWriteModel acepta un evento valido completo.

Given un body con todos los campos requeridos + opcionales,
When se instancia TrackingWriteModel,
Then todos los campos quedan accesibles con los tipos correctos.
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_message_model_accepts_valid_event() -> None:
    from models.message import TrackingWriteModel

    # Arrange
    body = valid_body(0)

    # Act
    msg = TrackingWriteModel(**body)

    # Assert
    assert msg.session_id == body['session_id']
    assert msg.page_id == body['page_id']
    assert msg.viewport_width == 1920
    assert msg.schema_version == 1
