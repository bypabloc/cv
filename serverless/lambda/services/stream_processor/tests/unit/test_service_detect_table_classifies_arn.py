"""Service stream_service.detect_table — clasificacion por ARN.

Given Stream records con distintos eventSourceARN,
When se invoca detect_table,
Then devuelve 'contacts', 'tracking' o 'unknown' segun el ARN.
"""

import pytest

from tests.unit._helpers import contact_record, tracking_record

pytestmark = pytest.mark.unit


def test_service_detect_table_classifies_arn():
    from services.stream_service import detect_table

    # Assert
    assert detect_table(contact_record('e1')) == 'contacts'
    assert detect_table(tracking_record('e2')) == 'tracking'
    assert detect_table({'eventSourceARN': 'arn:aws:other'}) == 'unknown'
    assert detect_table({}) == 'unknown'
