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

    def test_when_cf_token_too_short_then_raises(self) -> None:
        """Given cf_token < 20 chars, When parse, Then ValidationError."""
        with pytest.raises(PydanticValidationError):
            ContactFormInput(**self._valid_payload(cf_token='short'))  # noqa: S106

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
