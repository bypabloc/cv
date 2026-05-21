"""Service contact_service.process_contact_form — fallo del email.

Given que send_owner_email lanza una excepcion,
When se invoca process_contact_form,
Then el contacto queda persistido, se emite la metrica OwnerEmailFailed=1
     y NO se re-raise (la respuesta 201 del usuario no se rompe).
"""

import pytest

pytestmark = pytest.mark.unit


def test_contact_service_emits_metric_when_email_fails(monkeypatch):
    from services import contact_service
    from services.contact_service import process_contact_form

    # Arrange
    saved = {'contact_id': 'c-123', 'created_at': '2026-05-21T00:00:00Z'}
    monkeypatch.setattr(contact_service, 'save_contact', lambda _p: saved)

    def _raise(_contact):
        msg = 'SES boom'
        raise RuntimeError(msg)

    monkeypatch.setattr(contact_service, 'send_owner_email', _raise)
    contact_service.metrics.clear_metrics()

    # Act
    result = process_contact_form(
        form_fields={
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Hola mundo largo de prueba',
        }
    )

    # Assert
    captured = dict(contact_service.metrics.metric_set)
    assert result == saved
    assert captured['OwnerEmailFailed']['Value'] == [1.0]
