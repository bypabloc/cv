"""Service contact_service.process_contact_form — persiste y notifica.

Given un payload de form valido y el entorno AWS mockeado,
When se invoca process_contact_form,
Then el contacto queda persistido en Neon (con contact_id UUIDv7) y
     se envia el email al owner via SES (sin la metrica de fallo).

Spec direct-neon-writes: persistencia directa a Neon. Mockeamos
`insert_contact` y verificamos el payload exacto pasado al repository.
"""

import pytest

pytestmark = pytest.mark.unit


def test_contact_service_persists_and_sends_email(
    mock_neon_writes: list[dict], contact_form_aws: None
) -> None:
    from services import contact_service
    from services.contact_service import process_contact_form

    # Arrange
    contact_service.metrics.clear_metrics()

    # Act
    result = process_contact_form(
        form_fields={
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Hola mundo largo de prueba',
        }
    )

    # Assert: respuesta normalizada (UUID v7)
    assert len(result['contact_id']) == 36
    assert result['contact_id'][14] == '7'

    # Assert: una sola escritura a Neon con el payload esperado
    assert len(mock_neon_writes) == 1
    payload = mock_neon_writes[0]
    assert payload['id'] == result['contact_id']
    assert payload['name'] == 'Pablo'
    assert payload['email'] == 'p@example.com'
    assert payload['message'] == 'Hola mundo largo de prueba'
    # ip/country/user_agent son legacy: los contactos nuevos los reciben
    # en NULL (correlacion via session_id, SPEC-202).
    assert payload['ip'] is None
    assert payload['country'] is None
    assert payload['user_agent'] is None

    # Assert: el email se envio (no hay metrica de fallo)
    assert 'OwnerEmailFailed' not in dict(contact_service.metrics.metric_set)
