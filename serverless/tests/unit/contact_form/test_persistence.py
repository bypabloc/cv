"""Tests para contact_form.persistence."""

from __future__ import annotations

import boto3
import pytest

from contact_form.persistence import save_contact

pytestmark = pytest.mark.unit


class TestSaveContact:
    """save_contact - persist DynamoDB."""

    def test_when_valid_payload_then_returns_contact_id_uuid7(
        self, contact_form_aws: None
    ) -> None:
        """
        Given payload validado,
        When save_contact,
        Then retorna contact_id en formato UUIDv7 + persiste en DynamoDB.
        """
        result = save_contact({
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Hola mundo',
        })

        assert 'contact_id' in result
        assert len(result['contact_id']) == 36  # UUID format
        assert result['contact_id'][14] == '7'  # UUIDv7 marker
        assert 'created_at' in result

        # Verify persisted
        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-contacts-test'
        )
        item = table.get_item(Key={'id': result['contact_id']}).get('Item')
        assert item is not None
        assert item['name'] == 'Pablo'

    def test_when_optional_fields_present_then_stored(
        self, contact_form_aws: None
    ) -> None:
        """
        Given payload con company/role/budget,
        When save_contact,
        Then se guardan todos.
        """
        result = save_contact({
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Test',
            'company': 'Acme',
            'role': 'CTO',
            'budget': '$50k',
            'niche': 'fintech',
        })

        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-contacts-test'
        )
        item = table.get_item(Key={'id': result['contact_id']}).get('Item')
        assert item is not None
        assert item['company'] == 'Acme'
        assert item['role'] == 'CTO'
        assert item['budget'] == '$50k'
        assert item['niche'] == 'fintech'

    def test_when_optional_fields_none_or_empty_then_not_stored(
        self, contact_form_aws: None
    ) -> None:
        """
        Given payload con None/empty en opcionales,
        When save_contact,
        Then NO se guardan (DynamoDB no permite empty strings).
        """
        result = save_contact({
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Test',
            'company': None,
            'role': '',
        })

        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-contacts-test'
        )
        item = table.get_item(Key={'id': result['contact_id']}).get('Item')
        assert 'company' not in item  # type: ignore[operator]
        assert 'role' not in item  # type: ignore[operator]

    def test_when_session_id_present_then_stored(
        self, contact_form_aws: None
    ) -> None:
        """
        Given payload con session_id valido [AC-3],
        When save_contact,
        Then el item de contacts incluye session_id con ese valor.
        """
        session_id = 'a' * 32

        result = save_contact({
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Test',
            'session_id': session_id,
        })

        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-contacts-test'
        )
        item = table.get_item(Key={'id': result['contact_id']}).get('Item')
        assert item is not None
        assert item['session_id'] == session_id

    def test_when_session_id_absent_then_not_stored(
        self, contact_form_aws: None
    ) -> None:
        """
        Given payload sin session_id [AC-2],
        When save_contact,
        Then el item de contacts NO incluye session_id (se guarda igual).
        """
        result = save_contact({
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Test sin sesion',
        })

        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-contacts-test'
        )
        item = table.get_item(Key={'id': result['contact_id']}).get('Item')
        assert item is not None
        assert 'session_id' not in item

    def test_when_payload_has_origin_metadata_then_not_stored(
        self, contact_form_aws: None
    ) -> None:
        """
        Given payload que aun trae ip/country/user_agent [AC-3],
        When save_contact,
        Then el item de contacts NO incluye ninguno: contacts deja de
        duplicar datos de origen (se consultan via tracking_events).
        """
        result = save_contact({
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Test sin metadata de origen',
            'ip': '203.0.113.7',
            'country': 'CL',
            'user_agent': 'Mozilla/5.0',
        })

        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-contacts-test'
        )
        item = table.get_item(Key={'id': result['contact_id']}).get('Item')
        assert item is not None
        assert 'ip' not in item
        assert 'country' not in item
        assert 'user_agent' not in item
