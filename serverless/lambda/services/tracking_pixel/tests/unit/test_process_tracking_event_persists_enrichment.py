"""Service process_tracking_event — orquesta enrichment + persistencia.

Given un input validado, una IP y un User-Agent de Chrome,
When se invoca process_tracking_event,
Then el payload escrito a Neon contiene el browser/os/device parseados,
     la IP y el country code.

Spec direct-neon-writes: persistencia directa a Neon. Mockeamos
`insert_tracking` y verificamos el payload exacto pasado al repository.
"""

import pytest

from tests.unit._helpers import CHROME_UA, valid_body

pytestmark = pytest.mark.unit


def test_process_tracking_event_persists_enrichment(
    mock_neon_writes: list[dict], tracking_aws: None
) -> None:
    from services.tracking_service import process_tracking_event

    # Act
    process_tracking_event(
        validated_input=valid_body(),
        ip='1.2.3.4',
        user_agent=CHROME_UA,
        country='CL',
    )

    # Assert: una sola escritura a Neon con el enrichment correcto
    assert len(mock_neon_writes) == 1
    payload = mock_neon_writes[0]
    assert payload['browser'] == 'Chrome'
    assert payload['os'] == 'Linux'
    assert payload['device_type'] == 'desktop'
    assert payload['ip'] == '1.2.3.4'
    assert payload['country'] == 'CL'
