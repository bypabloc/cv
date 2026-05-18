"""Tests para contact_form.schemas (Pydantic validation)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from contact_form.schemas import ContactFormInput

pytestmark = pytest.mark.unit


class TestContactFormInput:
    """ContactFormInput - validacion Pydantic."""

    def _valid_payload(self, **overrides: object) -> dict:
        base = {
            'name': 'Pablo Contreras',
            'email': 'user@example.com',
            'message': 'Hola, me interesa colaborar en un proyecto.',
            'cf_token': 'x' * 30,
        }
        base.update(overrides)
        return base

    def test_when_valid_minimal_then_parses(self) -> None:
        """Given payload minimo, When ContactFormInput, Then valida."""
        parsed = ContactFormInput(**self._valid_payload())

        assert parsed.name == 'Pablo Contreras'
        assert parsed.email == 'user@example.com'

    def test_when_name_too_short_then_raises(self) -> None:
        """Given name < 2 chars, When parse, Then ValidationError."""
        with pytest.raises(PydanticValidationError):
            ContactFormInput(**self._valid_payload(name='X'))

    def test_when_message_too_short_then_raises(self) -> None:
        """Given message < 10 chars, When parse, Then ValidationError."""
        with pytest.raises(PydanticValidationError):
            ContactFormInput(**self._valid_payload(message='short'))

    def test_when_invalid_email_then_raises(self) -> None:
        """Given email invalido, When parse, Then ValidationError."""
        with pytest.raises(PydanticValidationError):
            ContactFormInput(**self._valid_payload(email='not-an-email'))

    def test_when_cf_token_empty_then_accepts(self) -> None:
        """
        Given cf_token vacio (default), When parse, Then accepts.
        El backend valida cf_token vs Turnstile en service layer; el schema
        permite vacio porque el bypass de tests E2E lo requiere.
        """
        parsed = ContactFormInput(**self._valid_payload(cf_token=''))
        assert parsed.cf_token == ''

    def test_when_message_has_html_then_sanitized(self) -> None:
        """Given message con HTML, When parse, Then escapado (XSS prevention)."""
        parsed = ContactFormInput(
            **self._valid_payload(message='Hola <script>alert(1)</script> hola hola')
        )

        assert '<script>' not in parsed.message
        assert '&lt;script&gt;' in parsed.message

    def test_when_invalid_service_type_then_raises(self) -> None:
        """Given service_type invalido, When parse, Then ValidationError."""
        with pytest.raises(PydanticValidationError):
            ContactFormInput(
                **self._valid_payload(service_type='invalid_type')
            )

    def test_when_optional_fields_omitted_then_none(self) -> None:
        """Given sin opcionales, When parse, Then todos None."""
        parsed = ContactFormInput(**self._valid_payload())

        assert parsed.company is None
        assert parsed.role is None
        assert parsed.service_type is None
        assert parsed.budget is None
        assert parsed.timeline is None
        assert parsed.niche is None
        assert parsed.session_id is None

    def test_when_session_id_omitted_then_none(self) -> None:
        """
        Given payload sin session_id [AC-2],
        When ContactFormInput parsea,
        Then session_id queda None (un visitante sin cf_session se acepta).
        """
        parsed = ContactFormInput(**self._valid_payload())

        assert parsed.session_id is None

    def test_when_session_id_valid_then_accepted(self) -> None:
        """
        Given un session_id de 32 chars (formato valido) [AC-1],
        When ContactFormInput parsea,
        Then session_id se acepta con ese valor exacto.
        """
        session_id = 'a' * 32

        parsed = ContactFormInput(
            **self._valid_payload(session_id=session_id)
        )

        assert parsed.session_id == session_id

    def test_when_session_id_min_length_then_accepted(self) -> None:
        """
        Given un session_id de exactamente 20 chars (limite inferior) [AC-1],
        When ContactFormInput parsea,
        Then se acepta.
        """
        session_id = 'b' * 20

        parsed = ContactFormInput(
            **self._valid_payload(session_id=session_id)
        )

        assert parsed.session_id == session_id

    def test_when_session_id_max_length_then_accepted(self) -> None:
        """
        Given un session_id de exactamente 64 chars (limite superior) [AC-1],
        When ContactFormInput parsea,
        Then se acepta.
        """
        session_id = 'c' * 64

        parsed = ContactFormInput(
            **self._valid_payload(session_id=session_id)
        )

        assert parsed.session_id == session_id

    def test_when_session_id_too_short_then_raises(self) -> None:
        """
        Given un session_id de 19 chars (< 20, formato invalido) [AC-4],
        When ContactFormInput parsea,
        Then ValidationError.
        """
        with pytest.raises(PydanticValidationError):
            ContactFormInput(**self._valid_payload(session_id='d' * 19))

    def test_when_session_id_too_long_then_raises(self) -> None:
        """
        Given un session_id de 65 chars (> 64, formato invalido) [AC-4],
        When ContactFormInput parsea,
        Then ValidationError.
        """
        with pytest.raises(PydanticValidationError):
            ContactFormInput(**self._valid_payload(session_id='e' * 65))
