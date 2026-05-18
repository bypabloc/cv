"""Tests del schema TrackingEventInput (campos requeridos, limites, UUID)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tracking_pixel.schemas import EVENT_PROPS_MAX_BYTES, TrackingEventInput

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
        Given un body con event_id y event_type_id UUID validos [AC-3],
        When se valida con Pydantic,
        Then ambos campos quedan en el modelo con su valor.
        """
        # Arrange / Act
        model = TrackingEventInput(**_base_body())

        # Assert
        assert model.event_id == _EVENT_ID
        assert model.event_type_id == _PAGE_LOAD

    def test_when_event_type_id_hyphenated_uuid_then_accepted(self) -> None:
        """
        Given event_id en forma con guiones (UUID4 de 36 chars) [AC-3],
        When se valida,
        Then se acepta (el validador tolera con/sin guiones).
        """
        # Arrange / Act
        model = TrackingEventInput(
            **_base_body(event_id='a1b2c3d4-e5f6-4718-a93a-4b5c6d7e8f90')
        )

        # Assert
        assert model.event_id == 'a1b2c3d4-e5f6-4718-a93a-4b5c6d7e8f90'

    def test_when_missing_event_type_id_then_validation_error(self) -> None:
        """
        Given un body sin event_type_id [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError (el handler -> 400 INVALID_INPUT).
        """
        # Arrange
        body = _base_body()
        del body['event_type_id']

        # Act / Assert
        with pytest.raises(ValidationError) as exc_info:
            TrackingEventInput(**body)
        assert 'event_type_id' in str(exc_info.value)

    def test_when_event_type_id_malformed_then_validation_error(self) -> None:
        """
        Given event_type_id con la longitud correcta pero no-UUID [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError (el validador UUID() rechaza).
        """
        # Arrange / Act / Assert: 36 chars con guiones, pero 'zzzz' no es hex
        with pytest.raises(ValidationError):
            TrackingEventInput(
                **_base_body(
                    event_type_id='zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz'
                )
            )

    def test_when_event_id_malformed_then_validation_error(self) -> None:
        """
        Given event_id con la longitud correcta pero no-UUID [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError.
        """
        # Arrange / Act / Assert: 32 chars pero 'g' no es hex valido
        with pytest.raises(ValidationError):
            TrackingEventInput(
                **_base_body(event_id='gggggggggggggggggggggggggggggggg')
            )


class TestTrackingEventInputRequiredFields:
    """TrackingEventInput - campos requeridos."""

    def test_when_missing_session_id_then_validation_error(self) -> None:
        """
        Given un body sin session_id [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError mencionando session_id.
        """
        # Arrange
        body = _base_body()
        del body['session_id']

        # Act / Assert
        with pytest.raises(ValidationError) as exc_info:
            TrackingEventInput(**body)
        assert 'session_id' in str(exc_info.value)

    def test_when_missing_event_id_then_validation_error(self) -> None:
        """
        Given un body sin event_id [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError mencionando event_id.
        """
        # Arrange
        body = _base_body()
        del body['event_id']

        # Act / Assert
        with pytest.raises(ValidationError) as exc_info:
            TrackingEventInput(**body)
        assert 'event_id' in str(exc_info.value)

    def test_when_missing_page_url_then_validation_error(self) -> None:
        """
        Given un body sin page_url [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError mencionando page_url.
        """
        # Arrange
        body = _base_body()
        del body['page_url']

        # Act / Assert
        with pytest.raises(ValidationError) as exc_info:
            TrackingEventInput(**body)
        assert 'page_url' in str(exc_info.value)


class TestTrackingEventInputLimits:
    """TrackingEventInput - limites de longitud y rango."""

    def test_when_session_id_too_short_then_validation_error(self) -> None:
        """
        Given session_id de 19 chars (min_length=20) [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            TrackingEventInput(**_base_body(session_id='x' * 19))

    def test_when_session_id_too_long_then_validation_error(self) -> None:
        """
        Given session_id de 65 chars (max_length=64) [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            TrackingEventInput(**_base_body(session_id='x' * 65))

    def test_when_page_url_too_long_then_validation_error(self) -> None:
        """
        Given page_url de 501 chars (max_length=500) [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError.
        """
        # Arrange
        long_url = 'https://x.com/' + 'a' * 500

        # Act / Assert
        with pytest.raises(ValidationError):
            TrackingEventInput(**_base_body(page_url=long_url))

    def test_when_viewport_width_negative_then_validation_error(self) -> None:
        """
        Given viewport_width=-1 (ge=0) [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            TrackingEventInput(**_base_body(viewport_width=-1))

    def test_when_viewport_height_above_max_then_validation_error(
        self,
    ) -> None:
        """
        Given viewport_height=10001 (le=10000) [AC-3],
        When se valida,
        Then Pydantic lanza ValidationError.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            TrackingEventInput(**_base_body(viewport_height=10001))


class TestTrackingEventInputOptionalFields:
    """TrackingEventInput - campos opcionales y defaults."""

    def test_when_only_required_fields_then_optionals_are_none(self) -> None:
        """
        Given un body solo con los campos requeridos [AC-3],
        When se valida,
        Then los campos opcionales quedan en None por default.
        """
        # Arrange / Act
        model = TrackingEventInput(**_base_body())

        # Assert
        assert model.page_title is None
        assert model.utm_source is None
        assert model.niche is None
        assert model.cf_token is None

    def test_when_all_optionals_given_then_accepted(self) -> None:
        """
        Given un body con todos los campos opcionales poblados [AC-3],
        When se valida,
        Then el modelo conserva cada valor.
        """
        # Arrange / Act
        model = TrackingEventInput(
            **_base_body(
                page_title='Home',
                page_path='/',
                referrer='https://google.com',
                utm_source='twitter',
                utm_medium='social',
                utm_campaign='launch',
                utm_content='hero',
                utm_term='portfolio',
                viewport_width=1920,
                viewport_height=1080,
                niche='vibe',
                cf_token='token-abc',  # noqa: S106 - Turnstile token, no es password
            )
        )

        # Assert
        assert model.page_title == 'Home'
        assert model.utm_medium == 'social'
        assert model.viewport_width == 1920
        assert model.niche == 'vibe'
        assert model.cf_token == 'token-abc'  # noqa: S105 - Turnstile token, no es password


class TestTrackingEventInputEventProps:
    """TrackingEventInput - validacion del campo opcional event_props."""

    def test_when_event_props_omitted_then_defaults_to_none(self) -> None:
        """
        Given un body de /track sin event_props [AC-10],
        When se valida,
        Then event_props queda en None (campo opcional).
        """
        model = TrackingEventInput(**_base_body())
        assert model.event_props is None

    def test_when_event_props_explicit_none_then_accepted(self) -> None:
        """
        Given un body con event_props pasado explicitamente como None [AC-10],
        When se valida (el validador de tamano corre sobre el valor None),
        Then event_props queda en None sin lanzar error.
        """
        model = TrackingEventInput(**_base_body(event_props=None))
        assert model.event_props is None

    def test_when_event_props_dict_then_accepted(self) -> None:
        """
        Given un body con event_props como dict de contexto del evento [AC-10],
        When se valida,
        Then event_props queda en el modelo con su contenido.
        """
        props = {'href': 'https://github.com/bypabloc', 'depth': 75}
        model = TrackingEventInput(**_base_body(event_props=props))
        assert model.event_props == props

    def test_when_event_props_within_size_limit_then_accepted(self) -> None:
        """
        Given event_props serializado justo en el limite de tamano [AC-11],
        When se valida,
        Then se acepta (el limite es inclusivo).
        """
        overhead = len('{"k":""}')
        filler = 'x' * (EVENT_PROPS_MAX_BYTES - overhead)
        model = TrackingEventInput(**_base_body(event_props={'k': filler}))
        assert model.event_props == {'k': filler}

    def test_when_event_props_exceeds_size_limit_then_validation_error(
        self,
    ) -> None:
        """
        Given event_props serializado que supera el tamano maximo [AC-11],
        When se valida,
        Then Pydantic lanza ValidationError (el handler -> 400 INVALID_INPUT).
        """
        overhead = len('{"k":""}')
        filler = 'x' * (EVENT_PROPS_MAX_BYTES - overhead + 1)
        with pytest.raises(ValidationError) as exc_info:
            TrackingEventInput(**_base_body(event_props={'k': filler}))
        assert 'event_props' in str(exc_info.value)
