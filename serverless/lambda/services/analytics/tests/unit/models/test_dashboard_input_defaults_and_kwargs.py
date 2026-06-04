"""
Given una request de dashboard sin bucket/limit explicitos,
When se valida DashboardInput,
Then bucket='day', limit=10 y date_to_exclusive = date_to + 1 dia
(datetime aware UTC).
"""

from datetime import UTC, datetime

from models.analytics import DashboardInput


def test_dashboard_input_defaults_and_date_to_exclusive():
    # Arrange
    raw = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }

    # Act
    parsed = DashboardInput.model_validate(raw)

    # Assert: defaults de bucket/limit
    assert parsed.bucket == 'day'
    assert parsed.limit == 10
    # Assert: rango half-open (date_to EXCLUSIVO = to + 1), datetime aware UTC
    assert parsed.date_from == datetime(2026, 4, 27, tzinfo=UTC)
    assert parsed.date_to == datetime(2026, 5, 27, tzinfo=UTC)
    assert parsed.date_to_exclusive() == datetime(2026, 5, 28, tzinfo=UTC)
