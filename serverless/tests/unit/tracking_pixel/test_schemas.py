"""Tests del schema TrackingEventInput (event_id + event_type_id)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tracking_pixel.schemas import TrackingEventInput

pytestmark = pytest.mark.unit

_SESSION_ID = 'session-uuid-1234567890abcdef'
_EVENT_ID = 'a1b2c3d4e5f60718293a4b5c6d7e8f90'
_PAGE_LOAD = '019e372b-e0a7-7154-8279-8829bcf6a08c'


def _base_body(**overrides: object) -> dict[str, object]:
    """Body minimo valido de /track, con overrides opcionales."""
    body: dict[str, object] = {
        'session_id': _SESSION_ID,
        'event_id': _EVENT_ID,
        'event_type_id': _PAGE_LOAD,
        'page_url': 'https://the-full-stack.com/',
    }
    body.update(overrides)
    return body


class TestTrackingEventInputEventIds:
    """TrackingEventInput - validacion de event_id / event_type_id."""

    def test_when_valid_event_ids_then_accepted(self) -> None:
        """
        Given un body con event_id y event_type_id UUID validos [AC-4],
        When se valida con Pydantic,
        Then ambos campos quedan en el modelo con su valor.
        """
        model = TrackingEventInput(**_base_body())

        assert model.event_id == _EVENT_ID
        assert model.event_type_id == _PAGE_LOAD

    def test_when_event_type_id_hyphenated_uuid_then_accepted(self) -> None:
        """
        Given event_id en forma con guiones (UUID4 de 36 chars) [AC-4],
        When se valida,
        Then se acepta (el validador tolera con/sin guiones).
        """
        model = TrackingEventInput(
            **_base_body(event_id='a1b2c3d4-e5f6-4718-a93a-4b5c6d7e8f90')
        )

        assert model.event_id == 'a1b2c3d4-e5f6-4718-a93a-4b5c6d7e8f90'

    def test_when_missing_event_type_id_then_validation_error(self) -> None:
        """
        Given un body sin event_type_id [AC-5],
        When se valida,
        Then Pydantic lanza ValidationError (el handler -> 400 INVALID_INPUT).
        """
        body = _base_body()
        del body['event_type_id']

        with pytest.raises(ValidationError) as exc_info:
            TrackingEventInput(**body)

        assert 'event_type_id' in str(exc_info.value)

    def test_when_event_type_id_malformed_then_validation_error(self) -> None:
        """
        Given event_type_id con la longitud correcta pero no-UUID [AC-6],
        When se valida,
        Then Pydantic lanza ValidationError (el validador UUID() rechaza).
        """
        # 36 chars, formato de guiones correcto, pero 'zzzz' no es hex.
        with pytest.raises(ValidationError):
            TrackingEventInput(
                **_base_body(
                    event_type_id='zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz'
                )
            )

    def test_when_event_id_malformed_then_validation_error(self) -> None:
        """
        Given event_id con la longitud correcta pero no-UUID [AC-6],
        When se valida,
        Then Pydantic lanza ValidationError.
        """
        # 32 chars pero 'g' no es un digito hexadecimal valido.
        with pytest.raises(ValidationError):
            TrackingEventInput(
                **_base_body(event_id='gggggggggggggggggggggggggggggggg')
            )
