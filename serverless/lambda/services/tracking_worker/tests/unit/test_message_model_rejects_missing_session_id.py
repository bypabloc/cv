"""
Given un body sin session_id,
When TrackingQueueMessage lo valida,
Then Pydantic lanza ValidationError mencionando el campo faltante.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.unit._helpers import valid_body


@pytest.mark.unit
def test_message_model_rejects_missing_session_id() -> None:
    # Arrange
    from models.message import TrackingQueueMessage

    body = valid_body()
    del body['session_id']

    # Act / Assert
    with pytest.raises(ValidationError) as exc:
        TrackingQueueMessage(**body)

    # session_id debe aparecer en los errores reportados.
    errors = exc.value.errors()
    missing_fields = [
        err['loc'][0] for err in errors if err['type'] == 'missing'
    ]
    assert 'session_id' in missing_fields
