"""Service stream_service.parse_contact_record — record no-INSERT.

Given un Stream record cuyo eventName no es INSERT,
When se invoca parse_contact_record,
Then devuelve None (solo se replican los INSERT).
"""

import pytest

from tests.unit._helpers import contact_record

pytestmark = pytest.mark.unit


def test_service_parse_contact_returns_none_for_non_insert():
    from services.stream_service import parse_contact_record

    # Arrange
    record = contact_record('evt-1')
    record['eventName'] = 'MODIFY'

    # Act
    result = parse_contact_record(record)

    # Assert
    assert result is None
