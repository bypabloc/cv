"""Modelo StreamModel.

Given un payload con una lista de Records del DynamoDB Stream,
When se valida con StreamModel,
Then 'records' queda accesible como la lista de records original.
"""

import pytest

from tests.unit._helpers import contact_record, tracking_record

pytestmark = pytest.mark.unit


def test_stream_model_accepts_batch_of_records():
    from models.stream import StreamModel

    # Arrange
    records = [contact_record('evt-1'), tracking_record('evt-2')]

    # Act
    model = StreamModel(records=records)

    # Assert
    assert model.records == records
