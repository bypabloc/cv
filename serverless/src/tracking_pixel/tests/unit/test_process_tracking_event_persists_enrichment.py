"""Service process_tracking_event — orquesta enrichment + persistencia.

Given un input validado, una IP y un User-Agent de Chrome,
When se invoca process_tracking_event,
Then el item persistido contiene el browser/os/device parseados y la IP.
"""

import boto3
import pytest

from tests.unit._helpers import CHROME_UA, valid_body

pytestmark = pytest.mark.unit


def test_process_tracking_event_persists_enrichment(tracking_aws: None):
    from services.tracking_service import process_tracking_event

    # Act
    result = process_tracking_event(
        validated_input=valid_body(),
        ip='1.2.3.4',
        user_agent=CHROME_UA,
        country='CL',
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
    assert item['browser'] == 'Chrome'
    assert item['os'] == 'Linux'
    assert item['device_type'] == 'desktop'
    assert item['ip'] == '1.2.3.4'
    assert item['country'] == 'CL'
