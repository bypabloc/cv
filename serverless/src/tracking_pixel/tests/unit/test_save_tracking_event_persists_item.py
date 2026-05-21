"""Service save_tracking_event — escritura del item en DynamoDB.

Given un payload de tracking con event_id y event_type_id,
When save_tracking_event escribe el item,
Then el item de DynamoDB contiene ambos identificadores del evento.
"""

import boto3
import pytest

from tests.unit._helpers import EVENT_ID, EVENT_TYPE_ID, SESSION_ID

pytestmark = pytest.mark.unit


def test_save_tracking_event_persists_item(tracking_aws: None):
    from services.tracking_service import save_tracking_event

    # Act
    result = save_tracking_event(
        {
            'session_id': SESSION_ID,
            'event_id': EVENT_ID,
            'event_type_id': EVENT_TYPE_ID,
            'page_url': 'https://the-full-stack.com/',
        }
    )

    # Assert
    table = boto3.resource('dynamodb', region_name='us-east-1').Table(
        'portfolio-tracking-test'
    )
    item = table.get_item(
        Key={
            'session_id': result['session_id'],
            'page_id': result['page_id'],
        }
    )['Item']
    assert item['event_id'] == EVENT_ID
    assert item['event_type_id'] == EVENT_TYPE_ID
