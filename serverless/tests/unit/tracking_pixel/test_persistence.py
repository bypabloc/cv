"""Tests de tracking_pixel.persistence (item DynamoDB con event ids)."""

from __future__ import annotations

import boto3
import pytest

from tracking_pixel.persistence import save_tracking_event

pytestmark = pytest.mark.unit

_SESSION_ID = 'session-uuid-1234567890abcdef'
_EVENT_ID = 'a1b2c3d4e5f60718293a4b5c6d7e8f90'
_PAGE_LOAD = '019e372b-e0a7-7154-8279-8829bcf6a08c'


class TestSaveTrackingEvent:
    """save_tracking_event - escritura del item en DynamoDB."""

    def test_when_event_ids_present_then_persisted_as_attributes(
        self, tracking_aws: None
    ) -> None:
        """
        Given un payload con event_id y event_type_id [AC-4],
        When save_tracking_event escribe el item,
        Then el item de DynamoDB contiene ambos atributos con su valor.
        """
        result = save_tracking_event(
            {
                'session_id': _SESSION_ID,
                'event_id': _EVENT_ID,
                'event_type_id': _PAGE_LOAD,
                'page_url': 'https://the-full-stack.com/',
            }
        )

        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-tracking-test'
        )
        item = table.get_item(
            Key={
                'session_id': result['session_id'],
                'page_id': result['page_id'],
            }
        )['Item']

        assert item['event_id'] == _EVENT_ID
        assert item['event_type_id'] == _PAGE_LOAD
