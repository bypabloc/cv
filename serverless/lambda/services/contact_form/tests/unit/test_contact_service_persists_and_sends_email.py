"""Service contact_service.process_contact_form — persiste y notifica.

Given un payload de form valido y el entorno AWS mockeado,
When se invoca process_contact_form,
Then el contacto queda persistido en DynamoDB (con contact_id UUIDv7) y
     se envia el email al owner via SES (sin la metrica de fallo).
"""

import boto3
import pytest

pytestmark = pytest.mark.unit


def test_contact_service_persists_and_sends_email(contact_form_aws):
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

    # Assert
    assert len(result['contact_id']) == 36
    assert result['contact_id'][14] == '7'
    table = boto3.resource('dynamodb', region_name='us-east-1').Table(
        'portfolio-contacts-test'
    )
    item = table.get_item(Key={'id': result['contact_id']}).get('Item')
    assert item['name'] == 'Pablo'
    assert 'OwnerEmailFailed' not in dict(contact_service.metrics.metric_set)
