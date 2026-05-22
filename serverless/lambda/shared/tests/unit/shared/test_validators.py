"""Unit tests para shared.validators."""

from __future__ import annotations

import pytest

from shared.validators import is_valid_country, is_valid_email, sanitize_text

pytestmark = pytest.mark.unit


class TestIsValidEmail:
    """is_valid_email - validacion de formato."""

    @pytest.mark.parametrize(
        'value',
        [
            'user@example.com',
            'user.name@example.com',
            'user+tag@example.com',
            'user-name@example.co.uk',
            'user_name@sub.example.com',
            '1@2.io',
        ],
    )
    def test_when_valid_email_then_returns_true(self, value: str) -> None:
        """Given email valido, When is_valid_email, Then True."""
        assert is_valid_email(value) is True

    @pytest.mark.parametrize(
        'value',
        [
            '',
            'not-an-email',
            'user@',
            '@example.com',
            'user @example.com',
            'user@example',  # sin TLD
            'user@example.c',  # TLD 1 char
            'user@.com',
        ],
    )
    def test_when_invalid_email_then_returns_false(self, value: str) -> None:
        """Given email invalido, When is_valid_email, Then False."""
        assert is_valid_email(value) is False

    def test_when_email_longer_than_254_chars_then_returns_false(self) -> None:
        """
        Given email mas largo que limite RFC 5321 (254),
        When is_valid_email,
        Then False.
        """
        long_email = 'a' * 250 + '@a.io'  # > 254
        assert is_valid_email(long_email) is False

    def test_when_non_string_input_then_returns_false(self) -> None:
        """Given input no-string, When is_valid_email, Then False."""
        assert is_valid_email(None) is False  # type: ignore[arg-type]
        assert is_valid_email(123) is False  # type: ignore[arg-type]


class TestIsValidCountry:
    """is_valid_country - ISO 3166-1 alpha-2."""

    @pytest.mark.parametrize('value', ['CL', 'US', 'PE', 'AR', 'MX'])
    def test_when_valid_iso_code_then_returns_true(self, value: str) -> None:
        """Given country code valido upper 2 chars, When is_valid_country, Then True."""
        assert is_valid_country(value) is True

    @pytest.mark.parametrize(
        'value',
        ['cl', 'USA', 'C', '', 'CLA', '12', 'C1'],
    )
    def test_when_invalid_format_then_returns_false(self, value: str) -> None:
        """Given country code invalido, When is_valid_country, Then False."""
        assert is_valid_country(value) is False


class TestSanitizeText:
    """sanitize_text - trim + HTML-escape + truncate."""

    def test_when_text_with_spaces_then_trims(self) -> None:
        """Given text con espacios alrededor, When sanitize, Then trimmed."""
        assert sanitize_text('  hello  ') == 'hello'

    def test_when_html_chars_then_escapes(self) -> None:
        """Given text con HTML chars, When sanitize, Then escaped."""
        result = sanitize_text('<script>alert(1)</script>')

        assert result == '&lt;script&gt;alert(1)&lt;/script&gt;'

    def test_when_max_length_then_truncates_before_escape(self) -> None:
        """
        Given text largo + max_length,
        When sanitize,
        Then trunca a max_length antes de escape.
        """
        assert sanitize_text('a' * 100, max_length=10) == 'aaaaaaaaaa'

    def test_when_quote_in_input_then_escapes(self) -> None:
        """Given text con comillas, When sanitize, Then escaped."""
        result = sanitize_text('say "hi" it\'s ok')

        assert '&quot;' in result
        assert '&#x27;' in result

    def test_when_non_string_then_returns_empty(self) -> None:
        """Given input no-string, When sanitize, Then empty string."""
        assert sanitize_text(None) == ''  # type: ignore[arg-type]
        assert sanitize_text(123) == ''  # type: ignore[arg-type]
