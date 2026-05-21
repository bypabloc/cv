"""Service stream_service.parse_tracking_record — imagen incompleta.

Given un Stream record tracking sin session_id en el NewImage,
When se invoca parse_tracking_record,
Then devuelve None (el record se saltea, no se replica).
"""

import pytest

from tests.unit._helpers import tracking_record

pytestmark = pytest.mark.unit


def test_service_parse_tracking_returns_none_without_keys():
    from services.stream_service import parse_tracking_record

    # Arrange
    record = tracking_record('evt-nokeys')
    del record['dynamodb']['NewImage']['session_id']

    # Act
    payload = parse_tracking_record(record)

    # Assert
    assert payload is None
