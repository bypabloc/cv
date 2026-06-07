"""
Given una request sin from/to,
When se valida DateRange,
Then date_to=medianoche de hoy (UTC) y date_from=hoy-30d, ambos datetime aware.
"""

from datetime import UTC, datetime, timedelta

from models._common import DateRange


def test_date_range_when_no_dates_then_defaults_30d():
    # Arrange
    raw = {}

    # Act
    parsed = DateRange.model_validate(raw)

    # Assert
    today_midnight = datetime.now(tz=UTC).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    assert parsed.date_to == today_midnight
    assert parsed.date_from == today_midnight - timedelta(days=30)
    assert parsed.to_has_time is False
