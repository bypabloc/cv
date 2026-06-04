"""TimeseriesInput acepta bucket=minute y valida la cardinalidad (AC-4).

Given un rango corto con bucket=minute,
When se valida TimeseriesInput,
Then se acepta. Un rango de minute mas largo que 48h se RECHAZA (cardinalidad).
"""

import pytest
from models.analytics import TimeseriesInput
from pydantic import ValidationError


def test_timeseries_bucket_minute_short_range_ok():
    # Arrange — 3h con bucket minute.
    raw = {
        'from': '2026-06-03T18:00:00Z',
        'to': '2026-06-03T21:00:00Z',
        'bucket': 'minute',
    }

    # Act
    parsed = TimeseriesInput.model_validate(raw)

    # Assert
    assert parsed.bucket == 'minute'
    assert parsed.to_has_time is True


def test_timeseries_bucket_minute_long_range_rejected():
    # Arrange — 30 dias con bucket minute (excede 48h).
    raw = {
        'from': '2026-05-01T00:00:00Z',
        'to': '2026-05-31T00:00:00Z',
        'bucket': 'minute',
    }

    # Act / Assert
    with pytest.raises(ValidationError):
        TimeseriesInput.model_validate(raw)


def test_timeseries_bucket_invalid_rejected():
    # Arrange — bucket no soportado.
    raw = {'from': '2026-06-03', 'to': '2026-06-03', 'bucket': 'second'}

    # Act / Assert
    with pytest.raises(ValidationError):
        TimeseriesInput.model_validate(raw)
