"""
Given una request sin from/to,
When se valida DateRange,
Then date_to=hoy y date_from=hoy-30d.
"""

from datetime import date, timedelta

from models._common import DateRange


def test_date_range_when_no_dates_then_defaults_30d():
    # Arrange
    raw = {}

    # Act
    parsed = DateRange.model_validate(raw)

    # Assert
    today = date.today()
    assert parsed.date_to == today
    assert parsed.date_from == today - timedelta(days=30)
