"""Modelo StreamModel.

Given un payload sin la clave 'records',
When se valida con StreamModel,
Then 'records' toma el default lista vacia.
"""

import pytest

pytestmark = pytest.mark.unit


def test_stream_model_defaults_records_to_empty():
    from models.stream import StreamModel

    # Act
    model = StreamModel()

    # Assert
    assert model.records == []
