"""Unit tests para shared.http.responses."""

from __future__ import annotations

import json

import pytest
from shared.core.exceptions import (
    IPBlacklistedError,
    RateLimitExceededError,
    ValidationError,
)
from shared.http.responses import (
    error_response,
    json_response,
    no_content_response,
    redirect_response,
)

pytestmark = pytest.mark.unit


class TestJsonResponse:
    """json_response - shape para API GW REST proxy."""

    def test_when_basic_call_then_returns_api_gw_shape(self) -> None:
        """
        Given status=200, body, origin,
        When json_response,
        Then retorna dict con statusCode/headers/body.
        """
        result = json_response(
            200, {'ok': True}, origin='https://the-full-stack.com'
        )

        assert result['statusCode'] == 200
        assert result['body'] == '{"ok":true}'
        assert (
            result['headers']['Access-Control-Allow-Origin']
            == 'https://the-full-stack.com'
        )

    def test_when_called_then_body_is_compact_json(self) -> None:
        """
        Given body dict,
        When json_response,
        Then body es JSON compacto (sin espacios).
        """
        result = json_response(
            201, {'id': 'abc', 'count': 42}, origin='https://the-full-stack.com'
        )

        assert ' ' not in result['body']  # compact JSON

    def test_when_security_headers_included_by_default(self) -> None:
        """
        Given respuesta normal,
        When json_response,
        Then incluye X-Content-Type-Options + X-Frame-Options + HSTS.
        """
        result = json_response(200, {}, origin='https://the-full-stack.com')

        assert result['headers']['X-Content-Type-Options'] == 'nosniff'
        assert result['headers']['X-Frame-Options'] == 'DENY'
        assert 'Strict-Transport-Security' in result['headers']

    def test_when_extra_headers_then_merged(self) -> None:
        """Given extra_headers, When json_response, Then merged."""
        result = json_response(
            200,
            {},
            origin='https://the-full-stack.com',
            extra_headers={'X-Custom': 'value'},
        )

        assert result['headers']['X-Custom'] == 'value'


class TestErrorResponse:
    """error_response - mapeo de ApplicationError a JSON."""

    def test_when_validation_error_then_400(self) -> None:
        """
        Given ValidationError,
        When error_response,
        Then statusCode=400.
        """
        err = ValidationError('Email invalido', code='INVALID_EMAIL')
        result = error_response(err, origin='https://the-full-stack.com')

        body = json.loads(result['body'])
        assert result['statusCode'] == 400
        assert body['code'] == 'INVALID_EMAIL'
        assert body['error'] == 'Email invalido'

    def test_when_rate_limit_error_then_429_with_retry_after_header(
        self,
    ) -> None:
        """
        Given RateLimitExceededError con retry_after=120,
        When error_response,
        Then statusCode=429 + header Retry-After=120.
        """
        err = RateLimitExceededError(
            'Too many requests',
            code='RATE_LIMIT_EXCEEDED',
            retry_after_seconds=120,
        )
        result = error_response(err, origin='https://the-full-stack.com')

        assert result['statusCode'] == 429
        assert result['headers']['Retry-After'] == '120'

    def test_when_ip_blacklist_error_then_403(self) -> None:
        """
        Given IPBlacklistedError,
        When error_response,
        Then statusCode=403, code=IP_BLACKLISTED.
        """
        err = IPBlacklistedError('IP banned', retry_after_seconds=86400)
        result = error_response(err, origin='https://the-full-stack.com')

        body = json.loads(result['body'])
        assert result['statusCode'] == 403
        assert body['code'] == 'IP_BLACKLISTED'

    def test_when_generic_exception_then_500_with_generic_message(self) -> None:
        """
        Given Exception generica (no ApplicationError),
        When error_response,
        Then statusCode=500 con mensaje generico (no leak).
        """
        err = ValueError('SECRET_DATABASE_LEAKED')
        result = error_response(err, origin='https://the-full-stack.com')

        body = json.loads(result['body'])
        assert result['statusCode'] == 500
        assert body['error'] == 'Internal server error'
        assert 'SECRET' not in body['error']  # no leak

    def test_when_application_error_with_extra_then_extra_included(self) -> None:
        """
        Given ApplicationError con extra dict,
        When error_response,
        Then body['extra'] preserva el dict.
        """
        err = ValidationError(
            'Validation failed',
            code='INVALID_FIELD',
            extra={'field': 'email'},
        )
        result = error_response(err, origin='https://the-full-stack.com')

        body = json.loads(result['body'])
        assert body['extra'] == {'field': 'email'}


class TestNoContentResponse:
    """no_content_response - 204 para fire-and-forget (tracking pixel)."""

    def test_when_called_then_204_empty_body(self) -> None:
        """
        Given origin,
        When no_content_response,
        Then statusCode=204, body vacio.
        """
        result = no_content_response(origin='https://the-full-stack.com')

        assert result['statusCode'] == 204
        assert result['body'] == ''
        assert (
            result['headers']['Access-Control-Allow-Origin']
            == 'https://the-full-stack.com'
        )


class TestRedirectResponse:
    """redirect_response - 302 con header Location (magic-link GET)."""

    def test_when_called_then_302_with_location_and_empty_body(self) -> None:
        """
        Given un location con fragment hash y un origin,
        When redirect_response,
        Then statusCode=302, header Location exacto y body vacio.
        """
        location = (
            'https://admin.portfolio.dev.the-full-stack.com/callback'
            '#access=tok&refresh=ref'
        )
        result = redirect_response(
            location, origin='https://admin.portfolio.dev.the-full-stack.com'
        )

        assert result['statusCode'] == 302
        assert result['headers']['Location'] == location
        assert result['body'] == ''

    def test_when_called_then_includes_cors_origin(self) -> None:
        """
        Given un origin,
        When redirect_response,
        Then echo del origin en Access-Control-Allow-Origin.
        """
        result = redirect_response(
            'https://admin.portfolio.dev.the-full-stack.com/callback#a=b',
            origin='https://admin.portfolio.dev.the-full-stack.com',
        )

        assert (
            result['headers']['Access-Control-Allow-Origin']
            == 'https://admin.portfolio.dev.the-full-stack.com'
        )

    def test_when_extra_headers_then_merged(self) -> None:
        """
        Given extra_headers,
        When redirect_response,
        Then los headers extra se incluyen sin pisar Location.
        """
        result = redirect_response(
            'https://admin.portfolio.dev.the-full-stack.com/callback#a=b',
            origin='https://admin.portfolio.dev.the-full-stack.com',
            extra_headers={'Cache-Control': 'no-store'},
        )

        assert result['headers']['Cache-Control'] == 'no-store'
        assert (
            result['headers']['Location']
            == 'https://admin.portfolio.dev.the-full-stack.com/callback#a=b'
        )

    def test_when_called_then_no_json_content_type(self) -> None:
        """
        Given un redirect sin body,
        When redirect_response,
        Then NO incluye Content-Type JSON (no hay body JSON).
        """
        result = redirect_response(
            'https://admin.portfolio.dev.the-full-stack.com/callback#a=b',
            origin='https://admin.portfolio.dev.the-full-stack.com',
        )

        assert 'Content-Type' not in result['headers']
