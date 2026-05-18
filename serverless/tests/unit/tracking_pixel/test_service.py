"""Tests de tracking_pixel.service (orquestacion enrichment + persist)."""

from __future__ import annotations

import boto3
import pytest

from tracking_pixel.service import process_tracking_event

pytestmark = pytest.mark.unit

_SESSION_ID = 'session-uuid-1234567890abcdef'
_EVENT_ID = 'a1b2c3d4e5f60718293a4b5c6d7e8f90'
_PAGE_LOAD = '019e372b-e0a7-7154-8279-8829bcf6a08c'
_CHROME_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    'Chrome/118.0.0.0 Safari/537.36'
)


def _validated_input(**overrides: object) -> dict[str, object]:
    """dict minimo del TrackingEventInput validado (sin cf_token)."""
    payload: dict[str, object] = {
        'session_id': _SESSION_ID,
        'event_id': _EVENT_ID,
        'event_type_id': _PAGE_LOAD,
        'page_url': 'https://the-full-stack.com/',
    }
    payload.update(overrides)
    return payload


def _tracking_table() -> object:
    """Devuelve el boto3 Table de tracking del entorno de test."""
    return boto3.resource('dynamodb', region_name='us-east-1').Table(
        'portfolio-tracking-test'
    )


class TestProcessTrackingEvent:
    """process_tracking_event - enrichment + persistencia."""

    def test_when_valid_input_then_returns_identifiers(
        self, tracking_aws: None
    ) -> None:
        """
        Given un input validado, una IP y un User-Agent [AC-3],
        When se invoca process_tracking_event,
        Then retorna session_id, page_id y expires_at del item persistido.
        """
        # Arrange / Act
        result = process_tracking_event(
            validated_input=_validated_input(),
            ip='1.2.3.4',
            user_agent=_CHROME_UA,
        )

        # Assert
        assert result['session_id'] == _SESSION_ID
        assert isinstance(result['page_id'], str)
        assert isinstance(result['expires_at'], int)

    def test_when_processed_then_enrichment_persisted(
        self, tracking_aws: None
    ) -> None:
        """
        Given un User-Agent de Chrome [AC-3],
        When process_tracking_event orquesta enrichment + persist,
        Then el item de DynamoDB contiene el browser/os/device parseados.
        """
        # Arrange / Act
        result = process_tracking_event(
            validated_input=_validated_input(),
            ip='1.2.3.4',
            user_agent=_CHROME_UA,
        )

        # Assert: el enrichment del UA quedo escrito en el item
        item = _tracking_table().get_item(
            Key={
                'session_id': result['session_id'],
                'page_id': result['page_id'],
            }
        )['Item']
        assert item['browser'] == 'Chrome'
        assert item['os'] == 'Linux'
        assert item['device_type'] == 'desktop'
        assert item['ip'] == '1.2.3.4'

    def test_when_country_given_then_persisted(
        self, tracking_aws: None
    ) -> None:
        """
        Given un country code provisto por CF-IPCountry [AC-3],
        When process_tracking_event lo recibe,
        Then el item persistido incluye el atributo country.
        """
        # Arrange / Act
        result = process_tracking_event(
            validated_input=_validated_input(),
            ip='1.2.3.4',
            user_agent=_CHROME_UA,
            country='CL',
        )

        # Assert
        item = _tracking_table().get_item(
            Key={
                'session_id': result['session_id'],
                'page_id': result['page_id'],
            }
        )['Item']
        assert item['country'] == 'CL'

    def test_when_no_country_then_attribute_absent(
        self, tracking_aws: None
    ) -> None:
        """
        Given country=None (default) [AC-3],
        When process_tracking_event persiste el evento,
        Then el item no contiene el atributo country.
        """
        # Arrange / Act
        result = process_tracking_event(
            validated_input=_validated_input(),
            ip='1.2.3.4',
            user_agent=_CHROME_UA,
        )

        # Assert
        item = _tracking_table().get_item(
            Key={
                'session_id': result['session_id'],
                'page_id': result['page_id'],
            }
        )['Item']
        assert 'country' not in item

    def test_when_user_agent_none_then_enrichment_is_unknown(
        self, tracking_aws: None
    ) -> None:
        """
        Given user_agent=None [AC-3],
        When process_tracking_event arma el payload,
        Then el item no escribe user_agent (string vacio es falsy y se omite)
        pero el enrichment queda como 'unknown'.
        """
        # Arrange / Act
        result = process_tracking_event(
            validated_input=_validated_input(),
            ip='1.2.3.4',
            user_agent=None,
        )

        # Assert: user_agent vacio no se escribe; enrichment queda 'unknown'
        item = _tracking_table().get_item(
            Key={
                'session_id': result['session_id'],
                'page_id': result['page_id'],
            }
        )['Item']
        assert 'user_agent' not in item
        assert item['browser'] == 'unknown'
        assert item['device_type'] == 'unknown'

    def test_when_event_ids_given_then_persisted(
        self, tracking_aws: None
    ) -> None:
        """
        Given un input con event_id y event_type_id [AC-3],
        When process_tracking_event persiste el evento,
        Then el item conserva ambos identificadores del evento.
        """
        # Arrange / Act
        result = process_tracking_event(
            validated_input=_validated_input(),
            ip='1.2.3.4',
            user_agent=_CHROME_UA,
        )

        # Assert
        item = _tracking_table().get_item(
            Key={
                'session_id': result['session_id'],
                'page_id': result['page_id'],
            }
        )['Item']
        assert item['event_id'] == _EVENT_ID
        assert item['event_type_id'] == _PAGE_LOAD
