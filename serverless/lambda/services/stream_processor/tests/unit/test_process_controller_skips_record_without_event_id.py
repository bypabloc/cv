"""Controller stream/process — record sin eventID.

Given un batch con un record sin eventID,
When el controller Process ejecuta su ciclo run(),
Then el record se cuenta como skipped y no se delega al service.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record

pytestmark = pytest.mark.unit


def test_process_controller_skips_record_without_event_id():
    from controllers.stream.process import Process

    # Arrange
    record = contact_record('')
    record['eventID'] = ''

    with patch(
        'controllers.stream.process.process_record'
    ) as mock_process:
        controller = Process(event={'records': [record]})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': True,
        'code': 0,
        'data': {
            'processed': 0,
            'skipped': 1,
            'failed_record_ids': [],
        },
    }
    assert mock_process.call_count == 0
