"""Controller stream/process — recoleccion de records fallidos.

Given un batch con un record OK y otro cuyo procesamiento lanza excepcion,
When el controller Process ejecuta su ciclo run(),
Then devuelve {is_valid: True, code: 0} y reporta solo el event_id
     fallido en failed_record_ids.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record

pytestmark = pytest.mark.unit


def _process_side_effect(record, event_id):
    if event_id == 'evt-bad':
        raise RuntimeError('simulated write failure')
    return 'processed'


def test_process_controller_collects_failed_records():
    from controllers.stream.process import Process

    # Arrange
    records = [contact_record('evt-ok'), contact_record('evt-bad')]
    with patch(
        'controllers.stream.process.process_record',
        side_effect=_process_side_effect,
    ):
        controller = Process(event={'records': records})

        # Act
        result = controller.run()

    # Assert
    assert result == {
        'is_valid': True,
        'code': 0,
        'data': {
            'processed': 1,
            'skipped': 0,
            'failed_record_ids': ['evt-bad'],
        },
    }
