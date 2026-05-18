"""Tests para stream_processor.transformers."""

from __future__ import annotations

import pytest

from stream_processor.transformers import (
    deserialize_image,
    detect_table,
    parse_contact_record,
    parse_tracking_record,
)

pytestmark = pytest.mark.unit


class TestDeserializeImage:
    def test_deserialize_string_and_number(self) -> None:
        """Given image type-tagged, When deserialize, Then valores Python."""
        image = {
            'id': {'S': 'abc123'},
            'count': {'N': '42'},
            'active': {'BOOL': True},
        }
        result = deserialize_image(image)
        assert result['id'] == 'abc123'
        assert int(result['count']) == 42
        assert result['active'] is True

    def test_empty_image_returns_empty_dict(self) -> None:
        """Given image vacio, When deserialize, Then {}."""
        assert deserialize_image({}) == {}


class TestParseContactRecord:
    def test_when_insert_event_then_returns_payload(self) -> None:
        """Given Stream record INSERT contacts, When parse, Then payload dict."""
        record = {
            'eventID': 'evt-001',
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'id': {'S': 'abc-uuid'},
                    'name': {'S': 'Pablo'},
                    'email': {'S': 'p@example.com'},
                    'message': {'S': 'hola'},
                    'created_at': {'S': '2026-05-14T15:00:00Z'},
                },
            },
        }
        result = parse_contact_record(record)
        assert result is not None
        assert result['id'] == 'abc-uuid'
        assert result['stream_event_id'] == 'evt-001'
        assert result['name'] == 'Pablo'

    def test_when_modify_event_then_returns_none(self) -> None:
        """Given MODIFY event, When parse, Then None (no procesamos)."""
        record = {
            'eventID': 'evt-002',
            'eventName': 'MODIFY',
            'dynamodb': {'NewImage': {'id': {'S': 'abc'}}},
        }
        assert parse_contact_record(record) is None

    def test_when_missing_id_then_returns_none(self) -> None:
        """Given INSERT sin id, When parse, Then None."""
        record = {
            'eventID': 'evt',
            'eventName': 'INSERT',
            'dynamodb': {'NewImage': {'name': {'S': 'X'}}},
        }
        assert parse_contact_record(record) is None

    def test_when_insert_with_session_id_then_payload_includes_it(
        self,
    ) -> None:
        """
        Given INSERT contacts con session_id en el image [AC-6],
        When parse_contact_record,
        Then el payload incluye session_id con ese valor (correlacion).
        """
        record = {
            'eventID': 'evt-003',
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'id': {'S': 'abc-uuid'},
                    'name': {'S': 'Pablo'},
                    'email': {'S': 'p@example.com'},
                    'message': {'S': 'hola'},
                    'session_id': {'S': 'a' * 32},
                },
            },
        }
        result = parse_contact_record(record)
        assert result is not None
        assert result['session_id'] == 'a' * 32

    def test_when_insert_then_legacy_origin_fields_are_null(self) -> None:
        """
        Given INSERT contacts (un image que aun trae ip/country/UA) [AC-6],
        When parse_contact_record,
        Then ip/country/user_agent del payload quedan None: contacts deja
        de poblar las columnas legacy para contactos nuevos.
        """
        record = {
            'eventID': 'evt-004',
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'id': {'S': 'abc-uuid'},
                    'name': {'S': 'Pablo'},
                    'email': {'S': 'p@example.com'},
                    'message': {'S': 'hola'},
                    'ip': {'S': '203.0.113.7'},
                    'country': {'S': 'CL'},
                    'user_agent': {'S': 'Mozilla/5.0'},
                },
            },
        }
        result = parse_contact_record(record)
        assert result is not None
        assert result['ip'] is None
        assert result['country'] is None
        assert result['user_agent'] is None

    def test_when_insert_without_session_id_then_payload_session_id_none(
        self,
    ) -> None:
        """
        Given INSERT contacts sin session_id en el image [AC-6],
        When parse_contact_record,
        Then session_id del payload queda None (contacto sin correlacion).
        """
        record = {
            'eventID': 'evt-005',
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'id': {'S': 'abc-uuid'},
                    'name': {'S': 'Pablo'},
                    'email': {'S': 'p@example.com'},
                    'message': {'S': 'hola'},
                },
            },
        }
        result = parse_contact_record(record)
        assert result is not None
        assert result['session_id'] is None


class TestParseTrackingRecord:
    def test_when_insert_then_returns_payload(self) -> None:
        """Given INSERT tracking, When parse, Then payload + viewport int."""
        record = {
            'eventID': 'evt-100',
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'session_id': {'S': 'sess-1'},
                    'page_id': {'S': 'page-uuid'},
                    'page_url': {'S': 'https://x.com'},
                    'viewport_width': {'N': '1920'},
                    'expires_at': {'N': '1750000000'},
                    'created_at': {'S': '2026-05-14T15:00:00Z'},
                },
            },
        }
        result = parse_tracking_record(record)
        assert result is not None
        assert result['session_id'] == 'sess-1'
        assert result['viewport_width'] == 1920
        assert result['expires_at'] == 1750000000

    def test_when_remove_event_then_returns_none(self) -> None:
        """Given REMOVE (TTL fired), When parse, Then None."""
        record = {
            'eventID': 'evt',
            'eventName': 'REMOVE',
            'dynamodb': {'OldImage': {'session_id': {'S': 's1'}}},
        }
        assert parse_tracking_record(record) is None

    def test_when_insert_with_event_ids_then_payload_includes_them(
        self,
    ) -> None:
        """
        Given INSERT tracking con event_id y event_type_id en el image [AC-7],
        When parse_tracking_record,
        Then el payload incluye ambos campos con su valor.
        """
        record = {
            'eventID': 'evt-101',
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'session_id': {'S': 'sess-2'},
                    'page_id': {'S': 'page-uuid-2'},
                    'page_url': {'S': 'https://x.com'},
                    'event_id': {'S': 'a1b2c3d4e5f60718293a4b5c6d7e8f90'},
                    'event_type_id': {
                        'S': '019e372b-e0a7-7154-8279-8829bcf6a08c'
                    },
                },
            },
        }
        result = parse_tracking_record(record)
        assert result is not None
        assert result['event_id'] == 'a1b2c3d4e5f60718293a4b5c6d7e8f90'
        assert result['event_type_id'] == (
            '019e372b-e0a7-7154-8279-8829bcf6a08c'
        )

    def test_when_insert_with_event_props_then_payload_includes_them(
        self,
    ) -> None:
        """
        Given INSERT tracking con event_props (Map de DynamoDB) [AC-10],
        When parse_tracking_record,
        Then el payload incluye event_props como dict Python.
        """
        record = {
            'eventID': 'evt-102',
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'session_id': {'S': 'sess-4'},
                    'page_id': {'S': 'page-uuid-4'},
                    'page_url': {'S': 'https://x.com'},
                    'event_props': {
                        'M': {'href': {'S': 'https://github.com/bypabloc'}}
                    },
                },
            },
        }
        result = parse_tracking_record(record)
        assert result is not None
        assert result['event_props'] == {'href': 'https://github.com/bypabloc'}

    def test_when_insert_without_event_props_then_payload_has_none(
        self,
    ) -> None:
        """
        Given INSERT tracking sin event_props en el image [AC-10],
        When parse_tracking_record,
        Then el payload tiene event_props en None (columna jsonb nullable).
        """
        record = {
            'eventID': 'evt-103',
            'eventName': 'INSERT',
            'dynamodb': {
                'NewImage': {
                    'session_id': {'S': 'sess-5'},
                    'page_id': {'S': 'page-uuid-5'},
                    'page_url': {'S': 'https://x.com'},
                },
            },
        }
        result = parse_tracking_record(record)
        assert result is not None
        assert result['event_props'] is None


class TestDetectTable:
    def test_when_contacts_arn_then_contacts(self) -> None:
        record = {
            'eventSourceARN': 'arn:aws:dynamodb:us-east-1:123:table/portfolio-contacts-dev/stream/x'
        }
        assert detect_table(record) == 'contacts'

    def test_when_tracking_arn_then_tracking(self) -> None:
        record = {
            'eventSourceARN': 'arn:aws:dynamodb:us-east-1:123:table/portfolio-tracking-dev/stream/x'
        }
        assert detect_table(record) == 'tracking'

    def test_when_unknown_arn_then_unknown(self) -> None:
        record = {
            'eventSourceARN': 'arn:aws:dynamodb:us-east-1:123:table/other/stream/x'
        }
        assert detect_table(record) == 'unknown'
