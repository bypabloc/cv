"""Modelo TrackingWriteModel rechaza un evento sin session_id.

Given un body sin el campo requerido `session_id`,
When se instancia TrackingWriteModel,
Then Pydantic lanza ValidationError.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_message_model_rejects_missing_session_id() -> None:
    from models.message import TrackingWriteModel

    # Arrange
    body = valid_body(0)
    del body['session_id']

    # Act / Assert
    with pytest.raises(ValidationError):
        TrackingWriteModel(**body)
