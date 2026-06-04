"""DateRange acepta datetime con hora y respeta el limite preciso (AC-3).

Given un from/to con hora explicita (ISO con T),
When se valida DateRange,
Then date_from/date_to son datetime aware UTC con la hora respetada y
  date_to_exclusive() NO suma 1 dia (el limite con hora es exclusivo directo).
"""

from datetime import UTC, datetime

from models._common import DateRange


def test_date_range_with_time_respects_hour():
    # Arrange — rango de 3 horas con hora explicita.
    raw = {'from': '2026-06-03T18:00:00Z', 'to': '2026-06-03T21:00:00Z'}

    # Act
    parsed = DateRange.model_validate(raw)

    # Assert
    assert parsed.date_from == datetime(2026, 6, 3, 18, 0, tzinfo=UTC)
    assert parsed.date_to == datetime(2026, 6, 3, 21, 0, tzinfo=UTC)
    assert parsed.to_has_time is True
    # Con hora: el limite es exclusivo directo (no +1 dia).
    assert parsed.date_to_exclusive() == datetime(
        2026, 6, 3, 21, 0, tzinfo=UTC,
    )


def test_date_range_date_only_is_retrocompatible():
    # Arrange — input solo-fecha (sin hora): convencion half-open intacta.
    raw = {'from': '2026-04-27', 'to': '2026-05-27'}

    # Act
    parsed = DateRange.model_validate(raw)

    # Assert
    assert parsed.date_from == datetime(2026, 4, 27, tzinfo=UTC)
    assert parsed.date_to == datetime(2026, 5, 27, tzinfo=UTC)
    assert parsed.to_has_time is False
    # Sin hora: el dia `to` queda incluido (to + 1 dia).
    assert parsed.date_to_exclusive() == datetime(2026, 5, 28, tzinfo=UTC)
