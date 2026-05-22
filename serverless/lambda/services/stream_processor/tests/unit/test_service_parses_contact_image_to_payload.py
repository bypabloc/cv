"""Service stream_service.parse_contact_record — transformacion de imagen.

Given un Stream record INSERT de contacts con NewImage type-tagged,
When se invoca parse_contact_record,
Then devuelve los kwargs de Contact con id, email y stream_event_id.
"""

import pytest

from tests.unit._helpers import contact_record

pytestmark = pytest.mark.unit


def test_service_parses_contact_image_to_payload():
    from services.stream_service import parse_contact_record

    # Arrange
    record = contact_record('evt-1')

    # Act
    payload = parse_contact_record(record)

    # Assert
    assert payload['id'] == 'contact-evt-1'
    assert payload['email'] == 'p@example.com'
    assert payload['stream_event_id'] == 'evt-1'
